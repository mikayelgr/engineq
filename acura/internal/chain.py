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

# Maximum number of retries for executing the workflow
MAX_RETRIES = 3

spotipy = Spotipy(
    auth_manager=SpotifyClientCredentials(
        client_id=Config().SPOTIFY_CLIENT_ID,
        client_secret=Config().SPOTIFY_CLIENT_SECRET
    )
)


@dataclass
class GraphState:
    retry_count: int = 0


@dataclass
class GraphDeps:
    sid: int
    pg: AsyncConnection

    class Config:
        arbitrary_types_allowed = True


@dataclass
class GenerateSearchQueryNode(BaseNode[GraphState, GraphDeps]):
    @dataclass
    class AgentOutput(BaseModel):
        query: str | None = Field(
            default=None,
            description="The search query to find tracks on Spotify.")
        exclude_explicit_tracks: bool = Field(
            default=True,
            description="Whether to exclude explicit tracks from the search results."
        )

    logger = logging.getLogger(__name__)
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
Generate concise, unique music search queries (each up to 4 words) based on a business owner's prompt describing their establishment and desired musical ambiance.

__CONSTRAINTS__
- Infer relevant musical attributes from the user's prompt, such as:
  - Genre
  - Mood
  - Tempo
  - Artist references
  - Era
  - Cultural influences
- Produce a SINGLE search query that:
  - Is no more than 4 words-long.
  - Is free from redundancy and repetition.
  - Targets unique musical aspects to ensure diverse search results and minimize duplication issues in the database.
- Maintains a professional tone aligned with business needs.
- Avoids extraneous or unrelated details.

__EXAMPLE__
*User Prompt:* "I own a modern coffee shop and want upbeat acoustic music to create a lively yet cozy atmosphere."

*Generated Search Queries:*
1. "Upbeat acoustic coffeehouse"
2. "Lively unplugged café tunes"
3. "Energetic acoustic ambiance"
"""
    )

    async def run(self, ctx: GraphRunContext[GraphState, GraphDeps]) -> 'SearchSpotifyNode' | End[None]:
        if ctx.state.retry_count > MAX_RETRIES:
            self.logger.error("Max retries exceeded for query generation.")
            return End(None)

        try:
            ambiance_prompt = (await ctx.deps.pg.execute(select(Prompts).where(Prompts.sid == ctx.deps.sid))).one()
            query_flow = await self.query_gen_agent.run(ambiance_prompt.prompt)
            # random character for truly random search query. for more information check the following
            # stackoverflow thread: https://stackoverflow.com/questions/68006378/spotify-api-randomness-in-search
            seed = random.choice(string.ascii_letters)
            query = query_flow.data.query + ' ' + seed
            return SearchSpotifyNode(query, query_flow.data.exclude_explicit_tracks)
        except Exception as e:
            self.logger.error(f"Error during query generation: {e}")
            ctx.state.retry_count += 1
            return GenerateSearchQueryNode()


@dataclass
class VerifyYoutubeNode(BaseNode[GraphState, GraphDeps]):
    """
    This node makes sure that the tracks from Spotify actually exist on YouTube by searching
    for them using Brave's search API. Tracks must be received from `search_spotify` tool in
    the workflow.
    """
    tracks: list[dict]
    logger = logging.getLogger(__name__)

    async def run(self, ctx: GraphRunContext[GraphState, GraphDeps]) -> GenerateSearchQueryNode | End[list[dict]]:
        for ti in range(len(self.tracks) - 1, -1, -1):
            t = self.tracks[ti]
            query = f"{t['name']} {t['artists'][0]['name']}"

            try:
                # It is virtually impossible to not get any results from YouTube from Brave
                # based on what we have seen so far.
                results = await BraveSearchService.search_youtube(query, 2)
            except Exception as e:
                self.logger.error(f"Error during Youtube verification: {e}")
                continue

            if len(results) == 0:
                self.logger.warning(f"No results found for '{query}'")
                # Removing the track at the index
                self.tracks.pop(ti)
                continue

            # Trigger the YoutubeAnalyzerAgent to check if the video is a music video
            # or contains music solely based on the title.
            if await YoutubeAnalyzerAgent().check_is_music_video(results[0]["title"]):
                self.tracks[ti] = {
                    "title": t["name"],
                    "uri": results[0]["url"],
                    "artist": t["artists"][0]["name"],
                    "duration": t["duration_ms"] / 1000,
                    "explicit": t.get("explicit", False),
                    "image": results[0].get("thumbnail", None).get("src", None),
                }

                continue

            # Removing the track at the index in case it is not a music video
            self.tracks.pop(ti)

        # If no tracks are left, we need to generate a new search query
        # and start the process again.
        if len(self.tracks) == 0:
            ctx.state.retry_count += 1
            return GenerateSearchQueryNode()

        return End(self.tracks)


@dataclass
class SearchSpotifyNode(BaseNode[GraphState, GraphDeps]):
    query: str  # Search query as generated by the GenerateSearchQueryNode.
    exclude_explicit_tracks: bool
    logger = logging.getLogger(__name__)

    async def run(self, _: GraphRunContext[GraphState, GraphDeps]) -> VerifyYoutubeNode | GenerateSearchQueryNode:
        try:
            # TODO: Analyze the titles and descriptions of the playlists and filter out the
            # most suitable ones for the given prompt of the user. This can be done using a
            # separate AI agent, which will take in the playlists and the prompt and
            # filter them out based on the prompt.
            #
            # Potential implementation start:
            # # search only for tracks for tracks on Spotify. uniqueness is almost guaranteed at this point
            # spotify_curated_playlists = spotipy.user_playlists("spotify")
            # if spotify_curated_playlists is None:
            #     self.logger.warning("Spotify API mishandled the request.")
            #     return End(None)

            spotify_search_response = spotipy.search(self.query, type="track")
            tracks = spotify_search_response["tracks"]["items"]
            if self.exclude_explicit_tracks:
                tracks = [t for t in tracks if not t["explicit"]]

            return VerifyYoutubeNode(tracks)
        except Exception as e:
            self.logger.error(f"Error during Spotify search: {e}")
            return GenerateSearchQueryNode()


@dataclass
class MusicDiscoveryPipeline:
    """
    MusicDiscoveryPipeline is responsible for orchestrating a series of nodes
    to facilitate the discovery of music. It utilizes a directed graph structure
    to define the flow of operations, where each node performs a specific task
    in the pipeline.

    Attributes:
        graph (Graph): A directed graph that defines the sequence of operations
            in the pipeline. The graph consists of the following nodes:
            - GenerateSearchQueryNode: Responsible for generating search queries
              based on input data.
            - SearchSpotifyNode: Executes the search query on Spotify to retrieve
              potential music matches.
            - VerifyYoutubeNode: Verifies the retrieved music matches by cross-referencing
              them with YouTube data.
            The graph is configured to produce a list of dictionaries as its final output.

    Methods:
        run(deps: GraphDeps) -> list[dict]:
            Executes the pipeline by running the graph with the specified dependencies.
            The pipeline starts with the `GenerateSearchQueryNode` and progresses through
            the defined nodes in the graph. If the graph execution does not produce any
            output, a `ValueError` is raised.

            Args:
                deps (GraphDeps): Dependencies required for the execution of the graph.
                    These may include external services, configurations, or other resources.

            Returns:
                list[dict]: The final output of the pipeline, which is a list of dictionaries
                containing the discovered music data.

            Raises:
                ValueError: If the graph execution does not produce any output.
    """

    graph = Graph(nodes=(GenerateSearchQueryNode, SearchSpotifyNode, VerifyYoutubeNode),
                  run_end_type=list[dict],
                  name="Music Discovery Pipeline")

    async def run(self, deps: GraphDeps):
        flow = await self.graph.run(
            GenerateSearchQueryNode(),
            state=GraphState(retry_count=0), deps=deps)
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
        flow = await MusicDiscoveryPipeline().run(deps=GraphDeps(sid=sid, pg=pg))
        return flow.output
    except Exception as e:
        raise Exception(f"Error during playlist generation: {e}")
