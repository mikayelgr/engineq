from pydantic_ai import Agent
from internal.models import Prompts
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncConnection
import logging
from dataclasses import dataclass
from internal.services.spotify import SpotifyService
from internal.services.brave_search import BraveSearchService
from internal.agents import decide_llm
from internal.agents.yt_analyzer_agent import YoutubeAnalyzerAgent
from pydantic_graph import BaseNode, GraphRunContext, End, Graph
import Levenshtein

# Maximum number of retries for executing the workflow
MAX_RETRIES = 3


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
    """
    Generates a concise search query based on the user's prompt.
    """
    logger = logging.getLogger(__name__)
    query_gen_agent = Agent(
        model=decide_llm(),
        retries=5,
        result_retries=3,
        result_type=str,
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
"""
    )

    async def run(self, ctx: GraphRunContext[GraphState, GraphDeps]) -> 'RetrieveSpotifyPlaylistsNode':
        try:
            ambiance_prompt = (await ctx.deps.pg.execute(select(Prompts).where(Prompts.sid == ctx.deps.sid))).one()
            flow = await self.query_gen_agent.run(ambiance_prompt.prompt)
            return RetrieveSpotifyPlaylistsNode(query=flow.data)
        except Exception as e:
            self.logger.error(f"Error during query generation: {e}")
            raise


@dataclass
class RetrieveSpotifyPlaylistsNode(BaseNode[GraphState, GraphDeps]):
    """
    Retrieves Spotify playlists.
    """
    query: str
    next_page_url: str | None = None

    async def run(self, _: GraphRunContext[GraphState, GraphDeps]) -> 'MatchSpotifyPlaylistNode':
        try:
            playlists = await SpotifyService.get_spotify_curated_playlists(next=self.next_page_url)
            if len(playlists.get("items", [])) == 0:
                return End(None)

            return MatchSpotifyPlaylistNode(query=self.query, playlists=playlists)
        except Exception as e:
            logging.getLogger(__name__).error(
                f"Error retrieving Spotify playlists: {e}")
            return End(None)


@dataclass
class MatchSpotifyPlaylistNode(BaseNode[GraphState, GraphDeps]):
    """
    Matches Spotify playlists against the generated query and filters tracks using an agent.
    """
    query: str
    playlists: dict

    playlist_filter_agent = Agent(
        model=decide_llm(),
        retries=3,
        result_retries=2,
        result_type=bool,
        model_settings={"temperature": 0.5},
        system_prompt="""
__CONTEXT__
You are an expert in understanding and interpreting playlist titles and descriptions
and inferring whether they might contain the music that a user might want from a
certain query.

__ASK__
Determine if a given playlist matches user's query or might include any music
which is related to user's request. The user will give you the query, as well
as the title and the description of the playlist.
"""
    )

    async def run(self, _: GraphRunContext[GraphState, GraphDeps]) -> 'SearchYoutubeNode' | End[None]:
        filtered_tracks = []
        selected_playlist = None

        for playlist in self.playlists.get("items", []):
            try:
                flow = await self.playlist_filter_agent.run(f"Desired Tracks in Playlist: {self.query}\nPlaylist title: {playlist['name']}\nPlaylist description: {playlist['description']}")
                is_playlist_match = flow.data
                if is_playlist_match:
                    selected_playlist = playlist
                    break

            except Exception as e:
                logging.getLogger(__name__).error(
                    f"Error filtering playlist '{playlist['name']}': {e}")

        if selected_playlist is not None:
            entries = await SpotifyService.get_playlist_entries_by_id(selected_playlist["id"])
            for entry in entries:
                track = entry.get("track")
                if not track.get("explicit", False):
                    filtered_tracks.append(track)
        else:
            logging.getLogger(__name__).warning(
                f"No matching playlists found for: '{self.query}'. Trying next page...")
            return RetrieveSpotifyPlaylistsNode(query=self.query, next_page_url=self.playlists.get("next"))

        if filtered_tracks:
            return SearchYoutubeNode(tracks=filtered_tracks)

        return End(None)


@dataclass
class SearchYoutubeNode(BaseNode[GraphState, GraphDeps]):
    """
    Searches YouTube for videos of the corresponding tracks.
    """
    tracks: list[dict]

    async def run(self, _: GraphRunContext[GraphState, GraphDeps]) -> 'VerifyYoutubeNode':
        tracks = []
        for track in self.tracks:
            query = f"{track['name']} {track['artists'][0]['name']}"
            try:
                results = await BraveSearchService.search_youtube(query, 2)
                # This data will be later used to verify if the video is a music video
                # when searching for the track on YouTube.
                tracks.append(
                    {"spotify_track": track, "youtube_results": results})
            except Exception as e:
                logging.getLogger(__name__).error(
                    f"Error searching YouTube for track '{track['name']}': {e}")
        return VerifyYoutubeNode(tracks)


@dataclass
class VerifyYoutubeNode(BaseNode[GraphState, GraphDeps]):
    """
    Verifies YouTube results to ensure they are music videos.
    """
    tracks: list[dict]

    async def run(self, _: GraphRunContext[GraphState, GraphDeps]) -> End[list[dict]]:
        verified_tracks = []
        for i in range(len(self.tracks)):
            spotify_track = self.tracks[i]["spotify_track"]
            youtube_results = self.tracks[i]["youtube_results"]
            for youtube_result in youtube_results:
                similarity = Levenshtein.ratio(
                    f"{spotify_track['name'].lower()} - {spotify_track['artists'][0]['name'].lower()}",
                    youtube_result["title"].lower()
                )

                # Here, we are using Levenshtein distance to check if the title of the
                # YouTube video is similar to the track name. If the similarity is above
                # a certain threshold (0.65), we consider it a match.
                #
                # This way, we don't need to trigger another LLM agent to check if the
                # video is a music video. We can assume that if the title is similar to
                # the track name, it is likely a music video.
                if youtube_result and similarity > 0.65:
                    verified_tracks.append({
                        "title": spotify_track["name"],
                        "uri": youtube_result["url"],
                        "artist": spotify_track["artists"][0]["name"],
                        "duration": spotify_track["duration_ms"] / 1000,
                        "explicit": spotify_track["explicit"],
                        "image": spotify_track.get("album", {}).get("images", [{}])[0].get("url", None),
                    })

                    break

        return End(verified_tracks)


@dataclass
class MusicDiscoveryPipeline:
    """
    Orchestrates the music discovery process.
    """
    graph = Graph(
        nodes=(GenerateSearchQueryNode, RetrieveSpotifyPlaylistsNode,
               MatchSpotifyPlaylistNode, SearchYoutubeNode, VerifyYoutubeNode),
        run_end_type=list[dict],
        name="Music Discovery Pipeline"
    )

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
