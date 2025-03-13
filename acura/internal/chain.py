from pydantic_ai import Agent
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.models.fallback import FallbackModel
from pydantic.dataclasses import dataclass
import requests
from pydantic import Field
from internal.models import Tracks, Playlists, Suggestions, Subscribers
from sqlalchemy import insert, select, func, literal_column
from sqlalchemy.ext.asyncio import AsyncConnection
from pydantic_ai import RunContext
from internal.conf import Config
from pydantic import BaseModel
import urllib.parse
import json

DISCOGS_PARAMS = {
    "token": Config().DISCOGS_USER_TOKEN,
    "per_page": 5
}


class WrappedSQLASession(BaseModel):
    session: AsyncConnection

    class Config:
        arbitrary_types_allowed = True


@dataclass
class Track:
    """
    Dataclass representing a music track with title, artist, and explicit flag
    to be used in the playlist generation.
    """

    title: str = Field(..., description="The title of the track.")
    artist: str = Field(..., description="The artist of the track.")
    explicit: bool = Field(
        False, description="Flag to indicate if the track is explicit.")


# We will be using a fallback model by default, since in the future we might change
# the primary model to something different than OpenAI.
model = FallbackModel(OpenAIModel(
    "gpt-4o", provider=OpenAIProvider(api_key=Config().OPENAI_API_KEY)))


@dataclass
class AgentDeps:
    db: WrappedSQLASession
    sid: int  # subscriber ID


agent = Agent(
    model,
    name="llm",
    retries=5,
    deps_type=AgentDeps,
    result_retries=5,
    result_type=bool)


async def process_track(ctx: RunContext[AgentDeps], t: Track):
    search_response = requests.get("https://api.discogs.com/database/search?" +
                                   urllib.parse.urlencode(DISCOGS_PARAMS) + '&' +
                                   urllib.parse.urlencode({"title": t.title, "artist": t.artist}))
    if search_response.status_code == 200:
        search_response_json = json.loads(search_response.content)
        if len(search_response_json["results"]) > 0:
            try:
                # Making sure that the playlist actually exists
                await ctx.deps.db.session.execute(insert(Playlists).values(
                    sid=ctx.deps.sid,
                    created_at=func.current_date()
                ))
            except:
                # At this point we definitely know that a playlist exists
                qr = await ctx.deps.db.session.execute(select(Playlists).where(
                    Playlists.sid == ctx.deps.sid,
                    Playlists.created_at == func.current_date()
                ).limit(1))
                playlist = qr.one()

                release = None
                for r in search_response_json["results"]:
                    if r["type"] == "release":
                        release = r
                if release is not None:
                    thumbnail = release["thumb"]
                    uri = release["resource_url"]
                    release_response = requests.get(
                        uri + '?' + urllib.parse.urlencode(DISCOGS_PARAMS))
                    if release_response.status_code == 200:
                        release_response_json = json.loads(
                            release_response.content)
                        if len(release_response_json["videos"]) > 0:
                            created_track = None
                            try:
                                qr = await ctx.deps.db.session.execute(insert(Tracks).values(
                                    title=release_response_json["title"],
                                    artist=release_response_json["artists_sort"],
                                    explicit=t.explicit,
                                    duration=release_response_json["videos"][0]["duration"],
                                    uri=release_response_json["videos"][0]["uri"],
                                    image=thumbnail
                                ).returning(literal_column('*')))
                                created_track = qr.one()
                            except:
                                # In case the track already exists
                                qr = await ctx.deps.db.session.execute(select(Tracks).where(
                                    Tracks.title == release_response_json["title"],
                                    Tracks.artist == release_response_json["artists_sort"]
                                ))

                                created_track = qr.one()

                            await ctx.deps.db.session.execute(insert(Suggestions).values(
                                pid=playlist.id,
                                tid=created_track.id,
                            ))

    search_response.close()


# @agent.tool(retries=3)
# async def search_web_for_trends(ctx: RunContext[AgentDeps], query: str):
#     """
#     This tool is responsible for searching the web for music trends based on a query
#     generated by the LLM, suitable for the specific business that we are working with.

#     Args:
#         ctx (RunContext): The RunContext object.
#         query (str): The query to search for (e.g. trendy music for restaurants).

#     Returns:
#         list[Track]: The list of tracks found in the search.
#     """

#     pass


@agent.tool(retries=3)
async def ensure_tracks_validity(ctx: RunContext[AgentDeps], tracks: list[Track]) -> bool:
    """
    This tool is responsible for verifying whether a track in a list of tracks exists,
    or is just a hallucination by the LLM. This is for enhanced search, and avoiding
    messy tracks. The tools is allowed to be retried 3 times in case of failure.

    Args:
        ctx (RunContext): The RunContext object.
        track_name (str): The name of the track to verify.
        artist_name (str): The name of the artist associated with the track.

    Returns:
        str: The response from the AI model.
    """

    for t in tracks:
        await process_track(ctx, t)

    return True


@agent.system_prompt
async def system_prompt(ctx: RunContext[AgentDeps]) -> str:
    """
    This function is responsible for generating the system prompt for the AI model.

    Args:
        ctx (RunContext): The RunContext object.

    Returns:
        str: The system prompt to be used by the AI model.
    """

    r = await ctx.deps.db.session.execute(
        select(Subscribers).where(Subscribers.id == ctx.deps.sid))
    # Retrieve the description of the business by the subscriber from the joined
    # prompts or settings table.
    sub = r.one()  # TODO: Finalize the implementation

    return """
    ## **Task**
    Generate a **4-song playlist** as a table. **Output only the data. No explanations, introductions, or additional text.**

    ## **Instructions**
    - The data must have exactly **50 rows** and **3 columns:**
    - **"Title"** (Song name)
    - **"Artist"** (Performer)
    - **"Explicit"** (`True` if explicit, otherwise `False`)

    - **Song selection criteria:**
    - **Avoid being too generic.**
    - **Balance mainstream and lesser-known tracks.**
    - **Include recent songs (2023-2025) when relevant.**
    - **Mark explicit songs correctly.** Assume `False` if uncertain.
    - **Ensure smooth flow** (no jarring genre/mood shifts).
    - **Use only real, commercially available songs.**

    Try hard to generate unique, trendy, and sometimes even hard to find releases.
    """


async def compose(sid: int, message: str, dbs: WrappedSQLASession) -> bool | None:
    """
    Compose a playlist based on the given message.
    """
    d = AgentDeps(dbs, sid)

    try:
        task = await agent.run(message, deps=d)
        return task.data
    except Exception as e:
        raise Exception("Error during playlist generation: ", e)
