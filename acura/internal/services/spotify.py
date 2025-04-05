from __future__ import annotations
from dataclasses import dataclass
import urllib.parse
import httpx
import datetime
from internal.conf import Config
import base64
from typing import Optional
import urllib
import logging

S_BASE_URL = "https://api.spotify.com/"
S_CLIENT_ID = Config().SPOTIFY_CLIENT_ID
S_CLIENT_SECRET = Config().SPOTIFY_CLIENT_SECRET


@dataclass
class SpotifyService:
    __bearer_token: Optional[str] = None
    __refresh_token: Optional[str] = None
    __token_expiration_date: Optional[datetime.datetime] = None
    _client: httpx.AsyncClient = httpx.AsyncClient(base_url=S_BASE_URL)
    # Singleton instance
    _instance: Optional[SpotifyService] = None

    @classmethod
    async def get_track_by_id(self, id: str) -> dict:
        """
        Get the track information by its ID from Spotify. In case of multiple
        IDs, the function will return an array.
        """

        # Check if the bearer token is expired or even exists. This is required
        # for all API calls.
        if self.__token_expired():
            await self.__set_token()

        # Example API call (replace with actual implementation)
        r = await self._client.get(
            f"/v1/tracks/{id}",
            headers={"Authorization": f"Bearer {self.__bearer_token}"}
        )

        r.raise_for_status()
        return r.json()["tracks"]

    @classmethod
    async def get_playlist_entries_by_id(self, id: str, next_url: str | None = None) -> tuple[list[dict], str | None]:
        # Check if the bearer token is expired or even exists. This is required
        # for all API calls.
        if self.__token_expired():
            await self.__set_token()

        # Set the target URL for the API call. If `next_url` is provided, use it
        # to get the next page of results. Otherwise, use the default URL.
        target_url = f"/v1/playlists/{id}/tracks"
        if next_url:
            parsed_url = urllib.parse.urlparse(next_url)
            path = parsed_url.path
            query = parsed_url.query
            target_url = path + "?" + query

        r = await self._client.get(
            target_url,
            params={"limit": 50},  # Default limit is 50 for now
            headers={"Authorization": f"Bearer {self.__bearer_token}"}
        )

        r.raise_for_status()
        return (r.json()["items"], r.json()["next"])

    @classmethod
    async def search_playlists(self, query: str | None = None, next_url: str | None = None) -> tuple[list[dict], str | None]:
        if (query is None) and (next_url is None):
            raise ValueError(
                "Either `query` or `next_url` must be provided to search playlists.")

        # Check if the bearer token is expired or even exists. This is required
        # for all API calls.
        if self.__token_expired():
            await self.__set_token()

        if next_url is not None:
            # Use the next URL to get the next page of results
            parsed_url = urllib.parse.urlparse(next_url)
            path = parsed_url.path
            query = parsed_url.query
            r = await self._client.get(
                path,
                params=query,
                headers={"Authorization": f"Bearer {self.__bearer_token}"}
            )
        else:
            r = await self._client.get(
                "/v1/search",
                params={"q": query, "type": "playlist", "limit": 10},
                headers={"Authorization": f"Bearer {self.__bearer_token}"}
            )

        r.raise_for_status()
        r = r.json()
        return (r["playlists"]["items"], r["playlists"]["next"])

    @classmethod
    def __token_expired(self) -> bool:
        """
        Check if the bearer token is expired or even exists.
        """
        if self.__bearer_token is None:
            return True
        return datetime.datetime.now() >= self.__token_expiration_date

    @classmethod
    async def __set_token(self):
        logging.info("Setting Spotify API token...")

        """
        Set the bearer token for the Spotify API client.
        """
        if self.__refresh_token:
            await self.__refresh_access_token()
        else:
            await self.__request_new_token()

    @classmethod
    async def __request_new_token(self):
        """
        Request a new access token using client credentials.
        """
        auth_str = S_CLIENT_ID + ':' + S_CLIENT_SECRET
        b64_auth_str = base64.b64encode(auth_str.encode()).decode()

        token_response = await self._client.post(
            "https://accounts.spotify.com/api/token",
            headers={"Authorization": f"Basic {b64_auth_str}"},
            data={"grant_type": "client_credentials"},
        )

        token_response.raise_for_status()
        token_data = token_response.json()
        self.__bearer_token = token_data["access_token"]
        self.__token_expiration_date = datetime.datetime.now(
        ) + datetime.timedelta(seconds=token_data["expires_in"])
        self.__refresh_token = token_data.get("refresh_token")

    @classmethod
    async def __refresh_access_token(self):
        """
        Refresh the access token using the refresh token.
        """
        auth_str = S_CLIENT_ID + ':' + S_CLIENT_SECRET
        b64_auth_str = base64.b64encode(auth_str.encode()).decode()

        token_response = await self._client.post(
            "https://accounts.spotify.com/api/token",
            headers={
                "Authorization": f"Basic {b64_auth_str}",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.__refresh_token,
                "scope": " ".join(["playlist-read-private"]),
            },
        )

        token_response.raise_for_status()
        token_data = token_response.json()
        self.__bearer_token = token_data["access_token"]
        self.__token_expiration_date = datetime.datetime.now(
        ) + datetime.timedelta(seconds=token_data["expires_in"])

        # Update the refresh token if a new one is provided
        if "refresh_token" in token_data:
            self.__refresh_token = token_data["refresh_token"]
