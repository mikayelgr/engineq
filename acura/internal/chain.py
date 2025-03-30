from spotipy import SpotifyClientCredentials
from pydantic_ai import Agent
from internal.models import Prompts, Tracks
from sqlalchemy import insert, select, func, literal_column
from sqlalchemy.ext.asyncio import AsyncConnection
from pydantic_ai import RunContext, ModelRetry
from pydantic import BaseModel, Field
from spotipy import Spotify as Spotipy
from datetime import datetime
from internal.models import Playlists, Suggestions
from httpx import AsyncClient
from internal.conf import Config
import logging
import random
import string
from internal.services.brave_search import BraveSearchService
from internal.agents import decide_llm
from internal.agents.yt_analyzer_agent import YoutubeAnalyzerAgent

logger = logging.getLogger(__name__)
spotipy = Spotipy(
    auth_manager=SpotifyClientCredentials(
        client_id=Config().SPOTIFY_CLIENT_ID,
        client_secret=Config().SPOTIFY_CLIENT_SECRET
    )
)


class AgentDeps(BaseModel):
    sid: int
    pg: AsyncConnection

    spotify_search_tracks: list

    class Config:
        arbitrary_types_allowed = True


class AgentOutput(BaseModel):
    """The final output returned by the agent."""

    done: bool = Field(
        default=True,
        description="Whether the agent has finished the workflow."
    )

    tracks: list


model = decide_llm()
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
1. Generate a good search query, preferably with some artist names included
2. Search for tracks on Spotify using `search_spotify` tool.
3. Pass the found tracks to `search_and_get_tracks_from_youtube` tool for enhanced search.
4. Complete

__ADDITIONAL CONTEXT__
- Today's date: **{datetime.today()}**.
""",
    deps_type=AgentDeps,
    result_retries=3,
    model_settings={
        "temperature": 0.8,
    },
    result_type=AgentOutput)


@agent.tool(retries=3)
async def search_spotify(ctx: RunContext[AgentDeps], query: str, exclude_explicit_tracks=True):
    """
    Search for tracks on Spotify based on the given query. You must ensure to fully pass
    the returned tracks to the next step in the workflow. Partial data is not accepted.

    Args:
        query: The search query to find tracks on Spotify.
        exclude_explicit_tracks: Whether to exclude explicit tracks from the search results.
    """

    # random character for truly random search query. for more information check the following
    # stackoverflow thread: https://stackoverflow.com/questions/68006378/spotify-api-randomness-in-search
    seed = random.choice(string.ascii_letters)
    query = query + ' ' + seed

    # search only for tracks for tracks on Spotify. uniqueness is almost guaranteed at this point
    spotify_search_response = spotipy.search(query, type="track")
    if ("tracks" not in spotify_search_response) or (len(spotify_search_response["tracks"]["items"]) == 0):
        return "No tracks were found. Try to improve/update the search query and try again."
    tracks = spotify_search_response["tracks"]["items"]
    if exclude_explicit_tracks:
        tracks = [t for t in tracks if not t["explicit"]]
    ctx.deps.spotify_search_tracks.extend(tracks)
    return "Spotify search completed successfully."


@agent.tool(retries=3)
async def search_tracks_from_youtube(ctx: RunContext[AgentDeps]) -> AgentOutput:
    """
    Make sure that the tracks from Spotify actually exist on YouTube by searching for them
    using Brave's search API. Tracks must be received from `search_spotify` tool in the
    workflow.
    """
    verified = []

    for t in ctx.deps.spotify_search_tracks:
        query = f"{t['name']} {t['artists'][0]['name']}"
        results = await BraveSearchService.search_youtube(query, 2)
        if results is None or len(results) == 0:
            continue

        # Trigger the YoutubeAnalyzerAgent to check if the video is a music video
        # or contains music solely based on the title.
        if await YoutubeAnalyzerAgent().check_is_music_video(results[0]["title"]):
            verified.append({
                "title": t["name"],
                "uri": results[0]["url"],
                "artist": t["artists"][0]["name"],
                "duration": t["duration_ms"] / 1000,
                # "explicit": t["explicit"],
                # "image": results[0]["thumbnail"]["src"],
            })

    if len(verified) == 0:
        return "No tracks were found. Try to improve/update the search query and try again."
    return AgentOutput(done=True, tracks=verified)


async def curate_music(sid: int, pg: AsyncConnection) -> AgentOutput:
    """
    Compose a playlist for the given subscriber ID.
    Args:
        sid: The subscriber ID.
        pg: The database connection.
        conf: The configuration object.
    """

    try:
        prompt = await __get_subscriber_prompt(pg, sid)
        if prompt is None:
            raise Exception(
                "No prompt found for the subscriber. At least one needs to be configured.")

        flow = await agent.run(prompt, deps=AgentDeps(pg=pg, sid=sid, spotify_search_tracks=[]))
        return flow.data.tracks
    except Exception as e:
        raise Exception(f"Error during playlist generation: {e}")


async def __get_subscriber_prompt(conn: AsyncConnection, sid: int) -> Prompts | None:
    try:
        r = await conn.execute(select(Prompts).where(Prompts.sid == sid))
        return r.one().prompt
    except:
        return None
