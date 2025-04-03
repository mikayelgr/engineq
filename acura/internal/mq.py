import json
import logging
import asyncio

import aio_pika
from aio_pika.abc import AbstractRobustConnection, AbstractIncomingMessage
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy import insert, select, func, literal_column

from internal.models import Subscribers, Playlists, Tracks, Suggestions
import internal.chain as chain

logger = logging.getLogger(__name__)


async def start_consuming(mq: AbstractRobustConnection, pg: AsyncConnection) -> None:
    """
    Establish a channel to the RabbitMQ queue and consume messages indefinitely,
    creating async tasks for each message to be processed.
    """
    logger.info("Starting the message consumption...")
    channel = await mq.channel()
    queue = await channel.declare_queue("acura", durable=True, auto_delete=False)
    tasks = set()

    async with queue.iterator() as iterator:
        try:
            async for message in iterator:
                task = asyncio.create_task(_process_message(message, pg))
                tasks.add(task)
                # Remove the task from our set when it's done
                task.add_done_callback(lambda t: tasks.discard(t))
                # Once the task has been added to the processing queue, we consider
                # it as acknowledged for now.
                await message.ack()
        except asyncio.CancelledError:
            logger.info("Message consumption cancelled.")
        finally:
            # Wait for all tasks to finish before returning
            logger.info("Waiting for all processing tasks to complete.")
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            logger.info("All message processing tasks completed.")


async def _process_message(msg: AbstractIncomingMessage, pg: AsyncConnection) -> None:
    """
    Process a single message from the queue. This includes validating the
    subscriber license, generating tracks, and updating the relevant playlist and
    track records in the database.
    """
    try:
        async with msg.process(ignore_processed=True):
            data = _parse_message(msg)
            license_key = data.get("license")
            if not license_key:
                raise ValueError("License key was not provided.")

            subscriber = await _get_subscriber(pg, license_key)
            if not subscriber:
                raise ValueError(
                    "No subscriber found with the given license.")

            # Generate or retrieve curated tracks
            try:
                tracks = await chain.curate(subscriber.id, pg)
            except Exception as e:
                raise RuntimeError(f"Error during track generation: {e}")

            # Create or retrieve today's playlist and add tracks
            try:
                playlist = await _create_or_get_playlist(pg, subscriber.id)
                await _add_tracks_to_playlist(pg, playlist.id, tracks)
            except Exception as e:
                logger.error(
                    "Error during playlist or track handling: %s", e, exc_info=True)

    except Exception as e:
        logger.error("AMQP Error During Processing: %s", e, exc_info=True)
        # Reject the message so it's not re-queued
        try:
            await msg.reject(requeue=False)
        except aio_pika.exceptions.MessageProcessError as mpe:
            logger.error("Message already processed: %s",
                         mpe, exc_info=True)


def _parse_message(msg: AbstractIncomingMessage) -> dict:
    """
    Safely parse the message body as JSON.
    """
    try:
        return json.loads(msg.body)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON body: {e}")


async def _get_subscriber(pg: AsyncConnection, license_key: str) -> Subscribers | None:
    """
    Retrieve the subscriber from the database based on the provided license key.
    """
    result = await pg.execute(select(Subscribers).where(Subscribers.license == license_key))
    return result.one_or_none()


async def _create_or_get_playlist(pg: AsyncConnection, subscriber_id: int) -> Playlists:
    """
    Create a new playlist for the current date or return the existing one.
    """
    try:
        # Attempt to create the playlist; if it already exists, handle in except block
        result = await pg.execute(
            insert(Playlists)
            .values(sid=subscriber_id, created_at=func.current_date())
            .returning(literal_column("id"))
        )
    except:
        # Fallback to selecting the existing playlist if the insert fails (e.g. unique constraint)
        result = await pg.execute(
            select(Playlists.id)
            .where(Playlists.sid == subscriber_id)
            .where(Playlists.created_at == func.current_date())
        )
    return result.one()


async def _add_tracks_to_playlist(pg: AsyncConnection, playlist_id: int, tracks: list[dict]) -> None:
    """
    Given a list of track data, create each track record (if possible)
    and link it to the playlist via the Suggestions table.
    """
    for track_data in tracks:
        track = await _create_track_from_spotify_search(pg, track_data)
        if track:
            await _add_track_to_suggestions(pg, playlist_id, track.id)


async def _create_track_from_spotify_search(pg: AsyncConnection, track_data: dict) -> Tracks | None:
    """
    Attempt to create a track in the database from the given track data.
    Return None if creation fails.
    """
    try:
        result = await pg.execute(
            insert(Tracks).values(
                title=track_data["title"],
                artist=track_data["artist"],
                duration=track_data["duration"],
                uri=track_data["uri"],
            ).returning(literal_column("*"))
        )
        return result.one()
    except Exception:
        logger.warning("Failed to create track: %s", track_data, exc_info=True)
        return None


async def _add_track_to_suggestions(pg: AsyncConnection, playlist_id: int, track_id: int) -> Suggestions:
    """
    Insert a record into the Suggestions table linking the playlist and track.
    """
    result = await pg.execute(
        insert(Suggestions)
        .values(pid=playlist_id, tid=track_id)
        .returning(literal_column("*"))
    )
    return result.one()
