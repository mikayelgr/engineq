import json
import sqlalchemy as db
from internal.models import Subscribers
import internal.chain as chain
from sqlalchemy.ext.asyncio import AsyncConnection
import aio_pika
import internal.conf
from internal.models import Playlists, Tracks, Suggestions
from sqlalchemy import insert, select, func, literal_column


async def consume(msg: aio_pika.abc.AbstractIncomingMessage, pg: AsyncConnection, conf: internal.conf.Config):
    try:
        parsed_message = json.loads(msg.body)
    except:
        raise Exception("Invalid JSON body provided in AMQP message")

    if ("license" not in parsed_message) or (parsed_message["license"] == "") or (parsed_message["license"] is None):
        raise Exception("License key was not provided")

    r = await pg.execute(db.select(Subscribers).where(Subscribers.license == parsed_message["license"]))
    s = r.one()
    if s is None:
        raise Exception("No subscriber found with the given license")

    try:
        tracks = await chain.curate_music(s.id, pg)
    except Exception as e:
        raise Exception(f"Something wrong happened during generation: {e}")

    try:
        playlist = await __create_or_get_playlist(pg, s.id)
        for t in tracks:
            track = await __create_track_from_spotify_search(pg, t)
            if track is not None:
                await __add_track_to_playlist(pg, playlist.id, track.id)
    except:
        pass


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
            duration=100,  # default for now
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
