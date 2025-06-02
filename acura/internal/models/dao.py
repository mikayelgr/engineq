from dataclasses import dataclass
from internal.models.codegen import Subscribers, Prompts, Playlists, Tracks, Suggestions
from internal.models.sql import SQLDatabase
from sqlalchemy import select, insert, func, literal_column, update, asc, text
import logging
from sqlalchemy.exc import IntegrityError
from asyncpg.exceptions import UniqueViolationError
from internal.services.embeddings import EmbeddingsService

logger = logging.getLogger(__name__)


@dataclass
class SubscribersDAO:
    @classmethod
    async def get_subscriber_by_license(cls, license: str):
        """
        Retrieve the subscriber from the database based on the provided license key.
        """
        async with SQLDatabase.connection() as pg:
            r = await pg.execute(select(Subscribers).where(Subscribers.license == license))
            return r.one_or_none()


@dataclass
class PromptsDAO:
    @classmethod
    async def get_subscriber_prompts_by_sid(cls, sid: int):
        """
        Retrieve the prompt from the database based on the provided prompt ID.
        """
        async with SQLDatabase.connection() as pg:
            r = await pg.execute(select(Prompts).where(Prompts.sid == sid))
            return r.all()


@dataclass
class PlaylistsDAO:
    @classmethod
    async def create_or_get_playlist(cls, sid: int):
        """
        Create a new playlist for the current date or return the existing one.
        """
        async with SQLDatabase.connection() as pg:
            try:
                # Attempt to create the playlist; if it already exists, handle in except block
                r = await pg.execute(
                    insert(Playlists)
                    .values(sid=sid, created_at=func.current_date())
                    .returning(literal_column("id"))
                )
            except IntegrityError as e:
                # Check if the error is due to a unique constraint violation
                if isinstance(e.orig, UniqueViolationError):
                    logger.warning("Playlist already exists for SID %s", sid)
                else:
                    logger.error("Failed to create playlist: %s", e)

                # Fallback to selecting the existing playlist if the insert fails
                r = await pg.execute(
                    select(Playlists.id)
                    .where(Playlists.sid == sid)
                    .where(Playlists.created_at == func.current_date())
                )
            return r.one_or_none()

    @classmethod
    async def add_track_to_playlist(cls, playlist_id: int, track_data: dict):
        """
        Given a list of track data, create each track record (if possible)
        and link it to the playlist via the Suggestions table.
        """
        if track := await TracksDAO.create_track(track_data):
            await SuggestionsDAO.add_track_to_suggestions(playlist_id, track.id)
            return track.id


@dataclass
class TracksDAO:
    @classmethod
    async def get_tracks_by_ids(cls, track_ids: list[int]):
        """
        Retrieve tracks from the database based on a list of track IDs.
        """
        async with SQLDatabase.connection() as pg:
            r = await pg.execute(select(Tracks.id).where(Tracks.id.in_(track_ids)))
            return r.all()

    @classmethod
    async def update_track_embedding(cls, track_id: int, embedding: list[float]):
        """
        Update the embedding for a given track ID.
        """
        async with SQLDatabase.connection() as pg:
            r = await pg.execute(
                update(Tracks)
                .where(Tracks.id == track_id)
                .values(search_embedding=embedding)
            )

            return r.rowcount

    @classmethod
    async def get_similar_track_ids(cls, search_embedding: list[float], sim_threshold: float = 0.5):
        """
        Retrieve tracks with a cosine distance less than 0.5 from the given embedding.
        """

        async with SQLDatabase.connection() as pg:
            r = await pg.execute(
                select(Tracks.id)
                .where(Tracks.search_embedding.cosine_distance(search_embedding) < sim_threshold)
                .order_by(asc(Tracks.search_embedding.cosine_distance(search_embedding))))

            return r.all()

    @classmethod
    async def n_similar_tracks_count(cls, search_embedding: list[float]):
        """
        Count the number of tracks with a cosine distance less than 0.5 from the given embedding.
        """

        async with SQLDatabase.connection() as pg:
            r = await pg.execute(
                select(func.count(Tracks.id))
                .where(Tracks.search_embedding.cosine_distance(search_embedding) < 0.5)
                .order_by(asc(Tracks.search_embedding.cosine_distance(search_embedding)))
            )

            return r.scalar_one_or_none()

    @classmethod
    async def create_track(cls, track_data: dict):
        """
        Attempt to create a track in the database from the given track data.
        Return None if creation fails.
        """
        try:
            async with SQLDatabase.connection() as pg:
                r = await pg.execute(
                    insert(Tracks).values(
                        title=track_data["title"],
                        artist=track_data["artist"],
                        duration=track_data["duration"],
                        uri=track_data["uri"],
                    ).returning(literal_column("*"))
                )
                return r.one_or_none()
        except IntegrityError as e:
            # Handle unique constraint violation or other integrity errors
            if isinstance(e.orig, UniqueViolationError):
                logger.warning("Track already exists: %s", track_data)
            else:
                logger.error("Failed to create track: %s", e)
            logger.warning("Failed to create track: %s", track_data)
            return None


@dataclass
class SuggestionsDAO:
    @classmethod
    async def get_past_n_hours_suggestions(cls, playlist_id: int, hours: int = 1):
        """
        Retrieve suggestions from the past specified hours for a given playlist.
        """

        async with SQLDatabase.connection() as pg:
            r = await pg.execute(
                select(Suggestions.pid, Suggestions.tid, Suggestions.added_at)
                .where(Suggestions.pid == playlist_id)
                .where(Suggestions.added_at > func.now() - text(f"INTERVAL '{hours} hours'"))
            )

            return r.all()

    @classmethod
    async def add_track_to_suggestions(cls, playlist_id: int, track_id: int):
        """
        Insert a record into the Suggestions table linking the playlist and track.
        """

        async with SQLDatabase.connection() as pg:
            r = await pg.execute(
                insert(Suggestions)
                .values(pid=playlist_id, tid=track_id)
                .returning(literal_column("*"))
            )

            return r.one_or_none()
