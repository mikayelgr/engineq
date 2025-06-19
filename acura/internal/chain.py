"""
EngineQ: An AI-enabled music management system.
Copyright (C) 2025  Mikayel Grigoryan

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

For inquiries, contact: michael.grigoryan25@gmail.com
"""

from pydantic_ai import Agent
import logging
from dataclasses import dataclass
from internal.services.spotify import SpotifyService
from internal.services.brave_search import BraveSearchService
from internal.agents import decide_llm
from pydantic_graph import BaseNode, GraphRunContext, End, Graph
import Levenshtein
from internal.models.dao import PromptsDAO, PlaylistsDAO, TracksDAO, SuggestionsDAO
from typing import Union
from internal.services.embeddings import EmbeddingsService

# Maximum number of retries for executing the workflow
MAX_RETRIES = 3


@dataclass
class GraphState:
    spotify_search_query: str | None = None

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
        model_settings={"temperature": 0.85, "top_p": 0.30},
        # The system prompts follow CodeSignal's MPF format for GenAI prompts.
        # Learn more here: https://codesignal.com/learn/paths/prompt-engineering-for-everyone?courseSlug=understanding-llms-and-basic-prompting-techniques&unitSlug=mastering-consistent-formatting-and-organization-for-effective-prompting
        system_prompt="""
Generate concise, unique music search queries based on a business owner's prompt describing their establishment and desired musical ambiance.

- Infer relevant musical attributes from the user's prompt and produce a search query that:
  - Is free from redundancy and repetition.
  - Targets unique musical aspects to ensure diverse search results and minimize duplication issues in the database.
  - Maintains a professional tone aligned with business needs.
  - Avoids extraneous or unrelated details.
  - Is unique every time.
"""
    )

    async def run(self, ctx: GraphRunContext[GraphState, GraphDeps]) -> "SourceSelectionRouterNode":
        if ctx.state.error_info:
            logging.getLogger(__name__).error(
                f"Error in previous step: {ctx.state.error_info}")
        if ctx.state.retry_count >= MAX_RETRIES:
            raise RuntimeError(
                f"Maximum retries ({MAX_RETRIES}) exceeded for query: `{ctx.state.spotify_search_query}`")

        try:
            prompts = await PromptsDAO.get_subscriber_prompts_by_sid(ctx.deps.sid)
            prompt = prompts[0].prompt
            flow = await self.query_gen_agent.run(prompt)
            ctx.state.spotify_search_query = flow.data
            return SourceSelectionRouterNode()
        except Exception as e:
            raise RuntimeError(f"Error during query generation: {e}")


@dataclass
class SearchSpotifyPlaylistsNode(BaseNode[GraphState, GraphDeps]):
    """
    Retrieves Spotify playlists.
    """

    async def run(self, ctx: GraphRunContext[GraphState, GraphDeps]) -> Union["MatchQueryWithSpotifyPlaylist", "GenerateSearchQueryNode"]:
        try:
            found_playlists, _ = await SpotifyService.search_playlists(query=ctx.state.spotify_search_query)
            if not found_playlists:
                ctx.state.retry_count += 1
                ctx.state.error_info = f"No playlists found for query: {ctx.state.spotify_search_query}"
                return GenerateSearchQueryNode()

            return MatchQueryWithSpotifyPlaylist(found_playlists)
        except Exception as e:
            raise RuntimeError(f"Error retrieving Spotify playlists: {e}")


@dataclass
class MatchQueryWithSpotifyPlaylist(BaseNode[GraphState, GraphDeps]):
    """
    Matches Spotify playlists against the generated query and filters tracks using an agent.
    """
    found_playlists: list[dict]

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

    async def run(self, ctx: GraphRunContext[GraphState, GraphDeps]) -> Union["SearchAndVerifyYoutubeAndSaveNode", "GenerateSearchQueryNode"]:
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
This is their search query: {ctx.state.spotify_search_query}
""")
                is_playlist_match = flow.data
                if is_playlist_match:
                    matched_playlist = playlist
                    break

            except Exception as e:
                logging.getLogger(__name__).error(
                    f"Error filtering playlist '{playlist['name']}']: {e}")

        if matched_playlist:
            pid = matched_playlist["id"]
            tracks = await SpotifyService.get_playlist_tracks(pid)
            return SearchAndVerifyYoutubeAndSaveNode(tracks=filter(lambda track: not track["explicit"], tracks))
        else:
            ctx.state.retry_count += 1
            ctx.state.error_info = f"No matching playlists found for query: {ctx.state.spotify_search_query}"
            return GenerateSearchQueryNode()


@dataclass
class SearchAndVerifyYoutubeAndSaveNode(BaseNode[GraphState, GraphDeps]):
    """
    Searches YouTube for videos of the corresponding tracks and verifies them to ensure they are music videos.
    """
    tracks: list[dict]

    async def run(self, ctx: GraphRunContext[GraphState, GraphDeps]) -> End:
        playlist = await PlaylistsDAO.create_or_get_playlist(ctx.deps.sid)
        n_added_tracks = 0

        for track in self.tracks:
            brave_search_query = f"{track['name']} {track['artists'][0]['name']}"
            try:
                results: list[dict] = await BraveSearchService.search_youtube_for_videos(brave_search_query)
                if not results:
                    continue

                for youtube_result in results:
                    similarity = Levenshtein.ratio(
                        f"{track['name'].lower()} - {track['artists'][0]['name'].lower()}",
                        youtube_result['title'].lower()
                    )

                    if youtube_result and (similarity > 0.75) and ("watch" in youtube_result["url"]):
                        embedding = await EmbeddingsService.create_track_embedding(
                            ctx.state.spotify_search_query,
                            track["name"],
                            track["artists"][0]["name"],
                        )

                        verified_track = {
                            "title": track["name"],
                            "uri": youtube_result["url"],
                            "artist": track["artists"][0]["name"],
                            "duration": track["duration_ms"],
                            "explicit": track["explicit"],
                            "image": track.get("album", {}).get("images", [{}])[0].get("url", None),
                        }

                        # Create the track in the database
                        tid = await PlaylistsDAO.add_track_to_playlist(playlist.id, verified_track)
                        # Add the track to suggestions
                        await TracksDAO.update_track_embedding(tid, embedding)
                        n_added_tracks += 1
                        break

            except Exception as e:
                raise RuntimeError(
                    f"Error searching and verifying YouTube for track '{track['name']}']: {e}")

        return End(n_added_tracks)


@dataclass
class SourceSelectionRouterNode(BaseNode[GraphState, GraphDeps]):
    """
    Decides whether to use existing data from the database or curate new data. This
    is one of the most important nodes in the system, since it decides whether to
    curate new data or use existing data, thus saving time and resources. As of
    right now, it is based on the date of last internet curation of a certain
    genre.

    The selection process depends on the following information:
    - The search query
        - The week of the last generation
        - The number of tracks curated for a specific genre
    """

    async def run(self, ctx: GraphRunContext[GraphState, GraphDeps]) -> Union["ReuseExistingDataNode", SearchSpotifyPlaylistsNode]:
        """
        Executes the logic to determine whether to reuse existing data or search for new Spotify playlists.

        Args:
            ctx (GraphRunContext[GraphState, GraphDeps]): The context containing the state and dependencies
            required for the execution.

        Returns:
            Union["ReuseExistingDataNode", SearchSpotifyPlaylistsNode]:
            - `ReuseExistingDataNode` if there are sufficient curations to reuse existing data.
            - `SearchSpotifyPlaylistsNode` if new data needs to be curated.

        Workflow:
            1. Creates a search query embedding using the Spotify search query from the context state.
            2. Retrieves similar track IDs based on the generated embedding.
            3. Fetches suggestions from the past hour using the provided dependency ID.
            4. Filters the past hour's suggestions to include only those that match the similar track IDs.
            5. Calculates the ratio of filtered suggestions to the total similar tracks.
            6. Determines whether to reuse existing data or curate new data based on the number of similar tracks
               and the calculated ratio.

        Notes:
            - The line `similar_track_ids = {t.tid for t in all_similar_tracks_cos}` creates a set of track IDs
              from the list of similar tracks for faster lookup during filtering.
        """

        search_embedding = await EmbeddingsService.create_search_query_embedding(ctx.state.spotify_search_query)
        all_similar_tracks_cos = await TracksDAO.get_similar_track_ids(search_embedding)
        past_1_hour_suggestions = await SuggestionsDAO.get_past_n_hours_suggestions(ctx.deps.sid)
        similar_track_ids = {t.id for t in all_similar_tracks_cos}
        suggestions_from_past_hour = [
            s for s in past_1_hour_suggestions if s.tid in similar_track_ids]
        ratio = len(suggestions_from_past_hour) / \
            len(all_similar_tracks_cos) if all_similar_tracks_cos else 0
        if (len(all_similar_tracks_cos) < 100) or (ratio > 0.5):
            return SearchSpotifyPlaylistsNode()
        return ReuseExistingDataNode(search_embedding=search_embedding)


@dataclass
class ReuseExistingDataNode(BaseNode[GraphState, GraphDeps]):
    search_embedding: list[float]

    """
    Reuses existing data from the database. This is one of the most important
    nodes in the system, since it decides whether to curate new data or use existing
    data, thus saving time and resources.
    """

    async def run(self, ctx: GraphRunContext[GraphState, GraphDeps]) -> End:
        """
        This function must use the `search_embedding` class variable. The steps are
        as follows:
        1. (similar_tracks) Get track IDs from the database that are most similar to `search_embedding`.
        2. Get the playlist ID from the database.
        3. Get the suggestions from the past hour.
        4. Filter the similar_tracks to make sure that the tracks from past hour are not included in the new suggestions.
        """

        # Step 1: Get track IDs most similar to `search_embedding`
        similar_tracks = await TracksDAO.get_similar_track_ids(self.search_embedding)
        # Step 2: Get the playlist ID from the database
        playlist = await PlaylistsDAO.create_or_get_playlist(ctx.deps.sid)
        # Step 3: Get the suggestions from the past hour
        past_hour_suggestions = await SuggestionsDAO.get_past_n_hours_suggestions(ctx.deps.sid)
        # Step 4: Filter similar_tracks to exclude tracks from past hour suggestions
        past_hour_track_ids = {
            suggestion.tid for suggestion in past_hour_suggestions}
        filtered_tracks = [
            track for track in similar_tracks if track.id not in past_hour_track_ids]

        # Add filtered tracks to the playlist
        n_added_tracks = 0
        for track in filtered_tracks:
            try:
                await SuggestionsDAO.add_track_to_suggestions(playlist.id, track.id)
                n_added_tracks += 1
            except Exception as e:
                logging.getLogger(__name__).error(
                    f"Error adding track '{track.title}' to playlist: {e}")

        return End(n_added_tracks)


@dataclass
class MusicDiscoveryPipeline:
    graph = Graph(
        nodes=(
            GenerateSearchQueryNode,
            SourceSelectionRouterNode,
            ReuseExistingDataNode,
            SearchSpotifyPlaylistsNode,
            MatchQueryWithSpotifyPlaylist,
            SearchAndVerifyYoutubeAndSaveNode
        ),
        name="Music Discovery Pipeline",
        run_end_type=int
    )

    async def run(self, deps: GraphDeps):
        flow = await self.graph.run(
            GenerateSearchQueryNode(),
            state=GraphState(),
            deps=deps,
        )

        return flow.output


async def curate(sid: int):
    """
    Curates a playlist for a given subscriber ID.
    """

    return await MusicDiscoveryPipeline().run(deps=GraphDeps(sid))
