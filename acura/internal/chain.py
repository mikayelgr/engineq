from pydantic_ai import Agent
import logging
from dataclasses import dataclass
from internal.services.spotify import SpotifyService
from internal.services.brave_search import BraveSearchService
from internal.agents import decide_llm
from pydantic_graph import BaseNode, GraphRunContext, End, Graph
import Levenshtein
from internal.models.dao import PromptsDAO, PlaylistsDAO, TracksDAO
from typing import Union

# Maximum number of retries for executing the workflow
MAX_RETRIES = 3


@dataclass
class GraphState:
    retry_count: int = 0
    error_info: str | None = None


@dataclass
class GraphDeps:
    sid: int


@dataclass
class GenerateSearchQueryNode(BaseNode[GraphState, GraphDeps]):
    """
    Generates a concise search query based on the user's prompt.
    """
    query_gen_agent = Agent(
        model=decide_llm(),
        retries=5,
        result_retries=3,
        result_type=str,
        name="GenerateSearchQueryAgent",
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

    async def run(self, ctx: GraphRunContext[GraphState, GraphDeps]) -> Union["SearchSpotifyPlaylistsNode", End]:
        if ctx.state.error_info:
            logging.getLogger(__name__).error(
                f"Error in previous step: {ctx.state.error_info}")
        if ctx.state.retry_count >= MAX_RETRIES:
            return End()

        try:
            prompts = await PromptsDAO.get_subscriber_prompts_by_sid(ctx.deps.sid)
            prompt = prompts[0].prompt
            flow = await self.query_gen_agent.run(prompt)
            return SearchSpotifyPlaylistsNode(flow.data)
        except Exception as e:
            logging.getLogger(__name__).error(
                f"Error during query generation: {e}")
            return End()


@dataclass
class SearchSpotifyPlaylistsNode(BaseNode[GraphState, GraphDeps]):
    """
    Retrieves Spotify playlists.
    """
    query: str | None

    async def run(self, ctx: GraphRunContext[GraphState, GraphDeps]) -> "MatchQueryWithSpotifyPlaylist":
        try:
            playlists, _ = await SpotifyService.search_playlists(query=self.query)
            if not playlists:
                ctx.state.retry_count += 1
                ctx.state.error_info = f"No playlists found for query: {self.query}"
                return GenerateSearchQueryNode()

            return MatchQueryWithSpotifyPlaylist(
                query=self.query,
                found_playlists=playlists,
            )
        except Exception as e:
            logging.getLogger(__name__).error(
                f"Error retrieving Spotify playlists: {e}")
            return End()


@dataclass
class MatchQueryWithSpotifyPlaylist(BaseNode[GraphState, GraphDeps]):
    """
    Matches Spotify playlists against the generated query and filters tracks using an agent.
    """
    query: str
    found_playlists: dict

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

    async def run(self, ctx: GraphRunContext[GraphState, GraphDeps]) -> Union["SearchYoutubeNode", "GenerateSearchQueryNode"]:
        matched_playlist = None

        for playlist in self.found_playlists:
            if playlist is None:
                continue

            try:
                flow = await self.playlist_filter_agent.run(f"""
__PLAYLIST INFO__
1. Title: {playlist['name']}
2. Description: {playlist['description']}

__ASK__
This is their query: {self.query}
""")
                is_playlist_match = flow.data
                if is_playlist_match:
                    matched_playlist = playlist
                    break

            except Exception as e:
                logging.getLogger(__name__).error(
                    f"Error filtering playlist '{playlist['name']}': {e}")

        if matched_playlist:
            pid = matched_playlist["id"]
            tracks = await SpotifyService.get_playlist_tracks(pid, 10)
            return SearchYoutubeNode(tracks=filter(lambda track: not track["explicit"], tracks))
        else:
            ctx.state.retry_count += 1
            ctx.state.error_info = f"No matching playlists found for query: {self.query}"
            return GenerateSearchQueryNode()


@dataclass
class SearchYoutubeNode(BaseNode[GraphState, GraphDeps]):
    """
    Searches YouTube for videos of the corresponding tracks.
    """
    tracks: list[dict]

    async def run(self, _: GraphRunContext[GraphState, GraphDeps]) -> 'VerifyAndSaveSuggestionsNode':
        tracks = []
        for track in self.tracks:
            query = f"{track['name']} {track['artists'][0]['name']}"
            try:
                results: list[dict] = await BraveSearchService.search_youtube_for_videos(query, 2)
                if not results:
                    logging.getLogger(__name__).warning(
                        f"No YouTube results found for track '{track['name']}'")
                    continue

                # TODO: Implement duration analysis for tracks, so that the playlist
                # doesn't get cluttered with tracks which are either shorts, etc.
                # for r in results:
                #     if ("video" not in r) or ("duration" not in r["video"]):
                #         # Skip results which don't have metadata about the video
                #         continue
                #
                #     video_duration_ms = self.parse_time_to_milliseconds(
                #         r["video"]["duration"])
                #     if video_duration_ms < 60 * 1000:
                #         # Skip videos which are shorter than 1 minute
                #         continue
                #     if video_duration_ms > track["duration_ms"] * 1.5:
                #         # Skip videos which are longer than 1.5 times the track duration
                #         continue
                #     correct_youtube_results.append(r)
                # if not correct_youtube_results:
                #     logging.getLogger(__name__).warning(
                #         f"No valid YouTube results found for track '{track['name']}'")
                #     continue

                # This data will be later used to verify if the video is a music video
                # when searching for the track on YouTube.
                tracks.append(
                    {"spotify_track": track, "search_results": results})
            except Exception as e:
                logging.getLogger(__name__).error(
                    f"Error searching YouTube for track '{track['name']}': {e}")

                # It is more beneficial to end early at this stage, because Brave's API
                # is much more expensive, so it would not make sense to continue searching
                # in case an error occurs and waste credits for other APIs.
                return End()

        return VerifyAndSaveSuggestionsNode(tracks)


@dataclass
class VerifyAndSaveSuggestionsNode(BaseNode[GraphState, GraphDeps]):
    """
    Verifies YouTube results to ensure they are music videos.
    """
    tracks: list[dict]

    async def run(self, ctx: GraphRunContext[GraphState, GraphDeps]) -> End:
        playlist = await PlaylistsDAO.create_or_get_playlist(ctx.deps.sid)

        for i in range(len(self.tracks)):
            verified_track = None
            spotify_track = self.tracks[i]["spotify_track"]
            youtube_results = self.tracks[i]["search_results"]
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
                if youtube_result and similarity > 0.68:
                    verified_track = {
                        "title": spotify_track["name"],
                        "uri": youtube_result["url"],
                        "artist": spotify_track["artists"][0]["name"],
                        "duration": spotify_track["duration_ms"],
                        "explicit": spotify_track["explicit"],
                        "image": spotify_track.get("album", {}).get("images", [{}])[0].get("url", None),
                    }

                    break

            if verified_track:
                await PlaylistsDAO.add_track_to_playlist(playlist.id, verified_track)

        return End(None)


@dataclass
class MusicDiscoveryPipeline:
    """
    Orchestrates the music discovery process.
    """
    graph = Graph(
        nodes=(GenerateSearchQueryNode, SearchSpotifyPlaylistsNode,
               MatchQueryWithSpotifyPlaylist, SearchYoutubeNode, VerifyAndSaveSuggestionsNode),
        name="Music Discovery Pipeline",
        run_end_type=None
    )

    async def run(self, deps: GraphDeps):
        await self.graph.run(
            GenerateSearchQueryNode(),
            state=GraphState(retry_count=0),
            deps=deps,
        )


async def curate(sid: int):
    """
    Curates a playlist for a given subscriber ID.
    """

    try:
        await MusicDiscoveryPipeline().run(deps=GraphDeps(sid))
    except Exception as e:
        raise Exception(f"Error during playlist generation: {e}")
