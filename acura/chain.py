from pydantic_ai import Agent
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.models.fallback import FallbackModel
from pydantic.dataclasses import dataclass
import requests
from pydantic import Field
from models import Tracks, Playlists, Suggestions
from sqlalchemy import insert, select, func, literal_column
from sqlalchemy.ext.asyncio import AsyncConnection
from pydantic_ai import RunContext
from conf import Config
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


# class WorkflowOutput(BaseModel):
#     """
#     Dataclass representing the output of the workflow, which is a list of tracks.
#     """

#     tracks: list[Track] = Field(...,
#                                 description="The list of tracks in the playlist.")


# We will be using a fallback model by default, since in the future we might change
# the primary model to something different than OpenAI.
# if Config().PYTHON_ENV == "production":
model = FallbackModel(OpenAIModel(
    "gpt-4o", provider=OpenAIProvider(api_key=Config().OPENAI_API_KEY)))
# else:
#     print("using llama3.2")
#     print(Config().__dict__)
#     model = OpenAIModel("llama3.2:latest", provider=OpenAIProvider(
#         api_key="ollama", base_url=Config().OLLAMA_URL))


@dataclass
class AgentDeps:
    db: WrappedSQLASession
    sid: int  # subscriber ID


agent = Agent(
    model,
    system_prompt="""
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
    """,
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
                ctx.deps.db.session.execute(insert(Playlists).values(
                    sid=ctx.deps.sid,
                    created_at=func.current_date()
                )).scalar_one()
            except:
                # At this point we definitely know that a playlist exists
                playlist = ctx.deps.db.session.execute(select(Playlists).where(
                    Playlists.sid == ctx.deps.sid,
                    Playlists.created_at == func.current_date()
                ).limit(1)).scalar_one()

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
                                created_track = ctx.deps.db.session.execute(insert(Tracks).values(
                                    title=release_response_json["title"],
                                    artist=release_response_json["artists_sort"],
                                    explicit=t.explicit,
                                    duration=release_response_json["videos"][0]["duration"],
                                    uri=release_response_json["videos"][0]["uri"],
                                    image=thumbnail
                                ).returning(literal_column('*'))).first()
                            except:
                                # In case the track already exists
                                created_track = ctx.deps.db.session.execute(select(Tracks).where(
                                    Tracks.title == release_response_json["title"],
                                    Tracks.artist == release_response_json["artists_sort"]
                                )).scalar_one()

                            ctx.deps.db.session.execute(insert(Suggestions).values(
                                pid=playlist.id,
                                tid=created_track.id,
                            ))

    search_response.close()


@agent.tool(retries=3)
async def verify_tracks(ctx: RunContext[AgentDeps], tracks: list[Track]) -> bool:
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
        await process_track(t, ctx)

    return True


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
