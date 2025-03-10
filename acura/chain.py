import asyncio
from pydantic_ai import Agent
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.models.fallback import FallbackModel
from pydantic.dataclasses import dataclass
import discogs_client
from pydantic import BaseModel, Field

from conf import Config


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


class WorkflowOutput(BaseModel):
    """
    Dataclass representing the output of the workflow, which is a list of tracks.
    """

    tracks: list[Track] = Field(...,
                                description="The list of tracks in the playlist.")


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

llm = Agent(
    model,
    system_prompt="""
    ## **Task**
    Generate a **50-song playlist** as a table. **Output only the data. No explanations, introductions, or additional text.**

    ## **Instructions**
    - The data must have exactly **50 rows** and **3 columns:**
    - **"Title"** (Song name)
    - **"Artist"** (Performer)
    - **"Explicit"** (`True` if explicit, otherwise `False`)

    - **Song selection criteria:**
    - **Balance mainstream and lesser-known tracks.**
    - **Include recent songs (2023-2025) when relevant.**
    - **Mark explicit songs correctly.** Assume `False` if uncertain.
    - **Ensure smooth flow** (no jarring genre/mood shifts).
    - **Use only real, commercially available songs.**
    ```
    """,
    name="llm",
    retries=5,
    result_retries=5,
    result_type=WorkflowOutput)

dcl = discogs_client.Client(
    "ExampleApplication/0.1", user_token=Config().DISCOGS_USER_TOKEN)


@llm.tool_plain(retries=3)
def verify_tracks(tracks: list[Track]) -> list[Track]:
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

    confirmed_tracks = []
    for track in tracks:
        search_results = dcl.search(
            track.title, artist=track.artist, type="release")
        if search_results.count > 0:
            # Check if any result matches the track title and artist
            for result in search_results:
                if result.title.lower() == track.title.lower() and any(
                    artist.name.lower() == track.artist.lower() for artist in result.artists
                ):
                    confirmed_tracks.append(track)
                    break

    return WorkflowOutput(tracks=confirmed_tracks)


async def compose(message: str) -> WorkflowOutput | None:
    """
    Compose a playlist based on the given message.
    """

    try:
        r = await llm.run(message)
        return r.data
    except Exception as e:
        print(f"Error: {e}")
        return None
