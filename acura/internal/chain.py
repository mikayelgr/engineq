from spotipy import SpotifyClientCredentials
from pydantic_ai import Agent
from internal.models import Prompts
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncConnection
from pydantic import BaseModel, Field
from spotipy import Spotify as Spotipy
from internal.conf import Config
import logging
import random
from dataclasses import dataclass
import string
from internal.services.brave_search import BraveSearchService
from internal.agents import decide_llm
from internal.agents.yt_analyzer_agent import YoutubeAnalyzerAgent
from pydantic_graph import BaseNode, GraphRunContext, End, Graph
from pydantic_ai import ModelRetry

logger = logging.getLogger(__name__)
spotipy = Spotipy(
    auth_manager=SpotifyClientCredentials(
        client_id=Config().SPOTIFY_CLIENT_ID,
        client_secret=Config().SPOTIFY_CLIENT_SECRET
    )
)


@dataclass
class GraphDeps:
    sid: int
    pg: AsyncConnection

    class Config:
        arbitrary_types_allowed = True


@dataclass
class VerifyYoutubeNode(BaseNode[None, GraphDeps]):
    """
    This node makes sure that the tracks from Spotify actually exist on YouTube by searching
    for them using Brave's search API. Tracks must be received from `search_spotify` tool in
    the workflow.
    """
    tracks: list[dict]

    async def run(self, _: GraphRunContext[None, GraphDeps]) -> End[list[dict]]:
        verified = []
        for t in self.tracks:
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
            raise ModelRetry(
                "No tracks were found. Try to improve/update the search query and try again.")

        return End(verified)


@dataclass
class SearchSpotifyNode(BaseNode[None, GraphDeps]):
    @dataclass
    class AgentOutput(BaseModel):
        query: str | None = Field(
            default=None,
            description="The search query to find tracks on Spotify.")
        exclude_explicit_tracks: bool = Field(
            default=True,
            description="Whether to exclude explicit tracks from the search results."
        )

    prompt: str  # The prompt of the business owner.

    query_gen_agent = Agent(
        model=decide_llm(),
        retries=5,
        result_retries=3,
        result_type=AgentOutput,
        model_settings={"temperature": 0.7},
        # The system prompts follow CodeSignal's MPF format for GenAI prompts.
        # Learn more here: https://codesignal.com/learn/paths/prompt-engineering-for-everyone?courseSlug=understanding-llms-and-basic-prompting-techniques&unitSlug=mastering-consistent-formatting-and-organization-for-effective-prompting
        system_prompt="""
__ASK__
You are a Music Search Query Generation AI designed to assist business owners. Your task is to generate concise, unique music search queries based on the user's prompt, which describes their business context and musical preferences.

__CONTEXT__
- The user is a business owner seeking music for specific purposes such as:
  - Background ambiance for their establishment.
  - Music for corporate events.
  - Soundtracks for marketing campaigns.
- The user's prompt may include details like:
  - Business type (e.g., café, retail store, office).
  - Desired atmosphere or mood (e.g., relaxing, energetic).
  - Preferred genres, artists, eras, or tempos.

__CONSTRAINTS__
- Infer all relevant musical attributes from the user's prompt, including:
  - Genre
  - Mood
  - Tempo
  - Artist references
  - Era
  - Cultural influences
- Generate 1 search query that:
  - Are each under 100 words.
  - Are free from redundancy and repetition.
  - Target unique musical aspects to ensure diverse search results and minimize duplication issues in the database.
- Maintain a professional tone aligned with business needs.
- Avoid extraneous or unrelated details.

__EXAMPLE__
*User Prompt:* "I own a modern coffee shop and want upbeat acoustic music to create a lively yet cozy atmosphere."

*Generated Search Queries:*
1. "Upbeat acoustic tracks for coffee shop ambiance"
2. "Lively acoustic café background music"
3. "Energetic unplugged songs for modern coffeehouse"
"""
    )

    async def run(self, _: GraphRunContext[None, GraphDeps]) -> VerifyYoutubeNode:
        flow = await self.query_gen_agent.run(self.prompt)
        # random character for truly random search query. for more information check the following
        # stackoverflow thread: https://stackoverflow.com/questions/68006378/spotify-api-randomness-in-search
        seed = random.choice(string.ascii_letters)
        query = flow.data.query + ' ' + seed

        # search only for tracks for tracks on Spotify. uniqueness is almost guaranteed at this point
        spotify_search_response = spotipy.search(query, type="track")
        if ("tracks" not in spotify_search_response) or (len(spotify_search_response["tracks"]["items"]) == 0):
            return "No tracks were found. Try to improve/update the search query and try again."
        tracks = spotify_search_response["tracks"]["items"]
        if flow.data.exclude_explicit_tracks:
            tracks = [t for t in tracks if not t["explicit"]]

        return VerifyYoutubeNode(tracks)


@dataclass
class MusicCurationGraph:
    graph = Graph(nodes=(SearchSpotifyNode, VerifyYoutubeNode),
                  run_end_type=list[dict],
                  name="Music Curation Graph")

    async def run(self, prompt: str, deps: GraphDeps):
        flow = await self.graph.run(SearchSpotifyNode(prompt), deps=deps)
        if flow.output is None:
            raise ValueError("Graph execution did not produce any output.")
        return flow


async def curate(sid: int, pg: AsyncConnection) -> list[dict] | None:
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

        flow = await MusicCurationGraph().run(prompt, deps=GraphDeps(sid=sid, pg=pg))
        return flow.output
    except Exception as e:
        raise Exception(f"Error during playlist generation: {e}")


async def __get_subscriber_prompt(conn: AsyncConnection, sid: int) -> Prompts | None:
    try:
        r = await conn.execute(select(Prompts).where(Prompts.sid == sid))
        return r.one().prompt
    except:
        return None
