from pydantic_ai.models.openai import OpenAIModel
import os
from spotipy import SpotifyClientCredentials
from pydantic_ai import Agent
from pydantic.dataclasses import dataclass
from internal.models import Prompts, Tracks
from sqlalchemy import insert, select, func, literal_column
from sqlalchemy.ext.asyncio import AsyncConnection
from pydantic_ai import RunContext
from pydantic import BaseModel
from spotipy import Spotify
from datetime import datetime
from internal.models import Playlists, Suggestions
from httpx import AsyncClient
import internal.conf


class AgentDeps(BaseModel):
    sid: int  # subscriber ID
    pg: AsyncConnection
    http: AsyncClient
    conf: internal.conf.Config
    spotipy: Spotify  # authenticated spotipy object

    class Config:
        arbitrary_types_allowed = True


@dataclass
class AgentOutput:
    finished: bool


model = OpenAIModel(
    "gpt-4o-mini" if not os.getenv(
        "OLLAMA_MODEL_NAME") else os.getenv("OLLAMA_MODEL_NAME"),
    base_url=(os.getenv("OLLAMA_API_URL")
              if os.getenv("OLLAMA_API_URL") else None),
)

agent = Agent(
    model,
    name="llm",
    retries=5,
    system_prompt=f"""__PROMPT__
You are a helpful music research and playlist generation agent. Your task is to
search for tracks on Spotify based on the given prompt. You should find tracks
that match the prompt and store the processed tracks in the database. You may
use additional context to help you with the search. You must make sure that
the results you provide are relevant to the prompt.

__INSTRUCTIONS__
1. Given user instructions, generate the best query for searching music of
   the user's choice.
2. Search for tracks on Spotify based on the prompt.

__ADDITIONAL CONTEXT__
- Today's date: **{datetime.today()}**.
""",
    deps_type=AgentDeps,
    result_retries=3,
    result_type=AgentOutput)


@agent.tool(retries=3)
async def search_spotify(ctx: RunContext[AgentDeps], query: str, exclude_explicit_tracks=True) -> AgentOutput:
    spotify_tracks_response = ctx.deps.spotipy.search(
        query, limit=20, type="track")
    for t in spotify_tracks_response["tracks"]["items"]:
        is_playable = t["is_playable"]
        is_explicit = t["explicit"]  # special field from Spotify API
        if is_playable and (not exclude_explicit_tracks or not is_explicit):
            playlist = await __create_or_get_playlist(ctx.deps.pg, ctx.deps.sid)
            track = await __create_track_from_spotify(ctx.deps.pg, t)
            if track is not None:
                await __add_track_to_playlist(ctx.deps.pg, playlist.id, track.id)

    return AgentOutput(finished=True)


async def compose(sid: int, pg: AsyncConnection, conf: internal.conf.Config):
    try:
        spotipy = Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=conf.SPOTIFY_CLIENT_ID,
                client_secret=conf.SPOTIFY_CLIENT_SECRET
            )
        )

        prompt = await __get_subscriber_prompt(pg, sid)
        if prompt is None:
            raise Exception(
                "No prompt found for the subscriber. At least one needs to be configured.")

        async with AsyncClient() as http:
            await agent.run(prompt, deps=AgentDeps(pg=pg, sid=sid, spotipy=spotipy, http=http, conf=conf))
    except Exception as e:
        raise Exception(f"Error during playlist generation: {e}")


async def __get_subscriber_prompt(conn: AsyncConnection, sid: int) -> Prompts | None:
    try:
        r = await conn.execute(select(Prompts).where(Prompts.sid == sid))
        return r.one().prompt
    except:
        return None


async def __add_track_to_playlist(conn: AsyncConnection, pid: int, tid: int) -> Suggestions:
    r = await conn.execute(insert(Suggestions).values(
        pid=pid, tid=tid
    ).returning(literal_column('*')))
    return r.one()


async def __create_track_from_spotify(conn: AsyncConnection, t: dict) -> Tracks | None:
    try:
        r = await conn.execute(insert(Tracks).values(
            title=t["name"],
            artist=t["artists"][0]["name"],
            explicit=t["explicit"],
            duration=t["duration_ms"] / 1000,
            uri=f"https://open.spotify.com/embed/{t['uri'].split(':')[1]}/{t['uri'].split(':')[2]}",
            image=t["album"]["images"][0]["url"]
        ).returning(literal_column('*')))
        return r.one()
    except:
        return None


async def __create_or_get_playlist(conn: AsyncConnection, sid: int) -> Playlists:
    try:
        # Making sure that the playlist actually exists
        r = await conn.execute(insert(Playlists).values(
            sid=sid, created_at=func.current_date()
        ).returning(literal_column("id")))
    except:
        r = await conn.execute(select(Playlists).where(
            Playlists.sid == sid).where(
            Playlists.created_at == func.current_date()))
    return r.one()
