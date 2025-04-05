from openai import OpenAI
from dataclasses import dataclass


@dataclass
class TrackEmbeddingsService:
    """
    Provides methods to create embeddings for tracks using OpenAI's API.
    """
    _client: OpenAI = OpenAI()

    @classmethod
    def create_embedding(self, search_query: str, track_title: str, track_artist: str) -> list[float]:
        # In order to get accurate embeddings for the track, we need to
        # create a string that contains the search query, track title, and
        # track artist. This will help the model understand the context
        # of the track and generate accurate embeddings.
        embeddable = f"""
Search Query: {search_query}
Track Title: {track_title}
Track Artist: {track_artist}"""

        response = self._client.embeddings.create(
            model="text-embedding-3-large",
            input=embeddable,
            dimensions=1024,
        )

        embedding = response.data[0].embedding
        return embedding
