from dataclasses import dataclass
from internal.models.codegen import Subscribers, Prompts, Playlists, Tracks, Suggestions
from internal.models.sql import SQLDatabase
from sqlalchemy import select, insert, func, literal_column
import logging
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)


@dataclass
class SubscribersDAO:
    @classmethod
    async def get_subscriber_by_license(cls, license: str) -> Subscribers | None:
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
            except IntegrityError:
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


@dataclass
class TracksDAO:
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
        except IntegrityError:
            logger.warning("Failed to create track: %s", track_data)
            return None


@dataclass
class SuggestionsDAO:
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
