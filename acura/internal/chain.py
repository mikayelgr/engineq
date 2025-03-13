from pydantic_ai import Agent
from pydantic.dataclasses import dataclass
from pydantic import Field
from internal.models import Prompts, Tracks
from sqlalchemy import insert, select, func, literal_column
from sqlalchemy.ext.asyncio import AsyncConnection
from pydantic_ai import RunContext
from pydantic import BaseModel
from spotipy import Spotify
from datetime import datetime
from internal.models import Playlists, Suggestions

# DISCOGS_SEARCH_PARAMS = {
#     "headers": 5,
#     "token": 'AHNzflVBnMrTsCzARRwHjMbBDVAJUjvIeXoEkTQF',
# }

# BRAVE_SEARCH_HEADERS = {
#     "Accept": "application/json",
#     "X-Subscription-Token": 'BSAPHppWGfLPL_YjH_IcgqlycPXXgZ-'
# }


class WrappedSpotifyClient(BaseModel):
    conn: Spotify

    class Config:
        arbitrary_types_allowed = True


class WrappedSQLAClient(BaseModel):
    conn: AsyncConnection

    class Config:
        arbitrary_types_allowed = True


@dataclass
class AgentDeps:
    sid: int  # subscriber ID
    pg: WrappedSQLAClient
    spotipy: WrappedSpotifyClient  # authenticated spotipy object


@dataclass
class AgentOutput:
    finished: bool = Field(...,
                           title="Whether the agent has finished its execution")


agent = Agent(
    "gpt-4o-mini",
    name="llm",
    retries=5,
    system_prompt=f"""
__PROMPT__
You are a helpful music research and playlist generation agent. Your task is to
search for tracks on Spotify based on the given prompt. You should find tracks
that match the prompt and store the processed tracks in the database. You may
use additional context to help you with the search. You must make sure that
the results you provide are relevant to the prompt.

__INSTRUCTIONS__
1. Given user instructions, generate the best prompt for searching music of
   the user's choice.
2. Search for tracks on Spotify based on the prompt.
3. Analyze the tracks for their relevance and whether they match user's request.
4. Store the processed tracks in the database.

__ADDITIONAL CONTEXT__
- Today's date: **{datetime.today()}**.
""",
    deps_type=AgentDeps,
    result_retries=3,
    result_type=AgentOutput)


@agent.tool(retries=3)
async def search_spotify(
    ctx: RunContext[AgentDeps],
    query: str,
    offset: str = 0,
) -> AgentOutput:
    """
    Search for tracks on Spotify based on the given query and offset.
    """

    spotify_tracks_response = ctx.deps.spotipy.conn.search(
        query, limit=20, offset=offset, type="track")
    for t in spotify_tracks_response["tracks"]["items"]:
        if not t["is_playable"]:
            continue

        try:
            # Making sure that the playlist actually exists
            r = await ctx.deps.pg.conn.execute(insert(Playlists).values(
                sid=ctx.deps.sid,
                created_at=func.current_date()
            ).returning(literal_column("id")))
        except:
            r = await ctx.deps.pg.conn.execute(select(Playlists).where(
                Playlists.sid == ctx.deps.sid).where(
                Playlists.created_at == func.current_date()))

        playlist = r.one()
        try:
            qr = await ctx.deps.pg.conn.execute(insert(Tracks).values(
                title=t["name"],
                artist=t["artists"][0]["name"],
                explicit=t["explicit"],
                duration=t["duration_ms"] / 1000,
                uri=f"https://open.spotify.com/embed/{t['uri'].split(':')[1]}/{t['uri'].split(':')[2]}",
                image=t["album"]["images"][0]["url"]
            ).returning(literal_column('*')))
            added_track = qr.one()

            await ctx.deps.pg.conn.execute(insert(Suggestions).values(
                pid=playlist.id,
                tid=added_track.id,
            ))
        except Exception as e:
            print(f"Error during track insertion: {e}")
            pass

    return AgentOutput(finished=True)


async def compose(sid: int, pg: WrappedSQLAClient):
    try:
        from spotipy import SpotifyClientCredentials
        spotipy = WrappedSpotifyClient(conn=Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id="5d457b1b27d844ffa4419dfb5829c41a",
                client_secret="c266ecf55e5b4f0b8fa03293275b1ffa"
            )
        ))

        d = AgentDeps(pg=pg, sid=sid, spotipy=spotipy)
        r = await pg.conn.execute(select(Prompts).where(Prompts.sid == sid))
        p = r.one()
        await agent.run(p.prompt, deps=d)
    except Exception as e:
        raise Exception(f"Error during playlist generation: {e}")
