import json
import sqlalchemy as db
from internal.models import Subscribers
import internal.chain as chain
from sqlalchemy.ext.asyncio import AsyncConnection
import aio_pika
import asyncio
from internal.models import Playlists, Tracks, Suggestions
from sqlalchemy import insert, select, func, literal_column
import aio_pika
import os
import logging

# Limit concurrent message processing to `N_LOGICAL_CPUs` tasks
SEMAPHORE = asyncio.Semaphore(os.cpu_count())


async def start_consuming(mq: aio_pika.abc.AbstractRobustConnection, pg: AsyncConnection):
    chan = await mq.channel()
    queue = await chan.declare_queue("acura", durable=True, auto_delete=False)
    tasks = set()  # to keep track of messages being processed in parallel

    async with queue.iterator() as iterator:
        async for msg in iterator:
            # Create a task for each message
            task = asyncio.create_task(__consume_message(msg, pg))
            tasks.add(task)
            # Remove completed tasks from the set
            task.add_done_callback(tasks.discard)

            async def __consume_message(msg: aio_pika.abc.AbstractIncomingMessage, pg: AsyncConnection):
                """T
                Process a single RabbitMQ message and handle all operations.
                """

                async with SEMAPHORE:  # Use the semaphore here
                    try:
                        async with msg.process(ignore_processed=True):
                            try:
                                parsed_message = json.loads(msg.body)
                            except json.JSONDecodeError:
                                raise Exception(
                                    "Invalid JSON body provided in AMQP message")

                            if not parsed_message.get("license"):
                                raise Exception("License key was not provided")

                            r = await pg.execute(db.select(Subscribers).where(Subscribers.license == parsed_message["license"]))
                            s = r.one_or_none()
                            if s is None:
                                raise Exception(
                                    "No subscriber found with the given license")

                            try:
                                tracks = await chain.curate(s.id, pg)
                            except Exception as e:
                                raise Exception(
                                    f"Something wrong happened during generation: {e}")

                            try:
                                playlist = await __create_or_get_playlist(pg, s.id)
                                for t in tracks:
                                    track = await __create_track_from_spotify_search(pg, t)
                                    if track is not None:
                                        await __add_track_to_playlist(pg, playlist.id, track.id)
                            except Exception as e:
                                logging.getLogger(__name__).error(
                                    f"Error during playlist or track handling: {e}")

                            await msg.ack()
                    except Exception as e:
                        logging.getLogger(__name__).error(
                            "AMQP Error During Processing: %s", e)
                        try:
                            await msg.reject(requeue=False)
                        except aio_pika.exceptions.MessageProcessError as mpe:
                            logging.getLogger(__name__).error(
                                "Message already processed: %s", mpe)


async def __create_or_get_playlist(pg: AsyncConnection, sid: int) -> Playlists:
    try:
        # Making sure that the playlist actually exists
        r = await pg.execute(insert(Playlists)
                             .values(sid=sid, created_at=func.current_date())
                             .returning(literal_column("id")))
    except:
        r = await pg.execute(select(Playlists)
                             .where(Playlists.sid == sid)
                             .where(Playlists.created_at == func.current_date()))
    return r.one()


async def __create_track_from_spotify_search(pg: AsyncConnection, t: dict) -> Tracks | None:
    try:
        r = await pg.execute(insert(Tracks).values(
            title=t["title"],
            artist=t["artist"],
            duration=t["duration"],  # default for now
            uri=t["uri"],
        ).returning(literal_column('*')))
        return r.one()
    except Exception as e:
        return None


async def __add_track_to_playlist(pg: AsyncConnection, pid: int, tid: int) -> Suggestions:
    r = await pg.execute(insert(Suggestions)
                         .values(pid=pid, tid=tid)
                         .returning(literal_column('*')))
    return r.one()
