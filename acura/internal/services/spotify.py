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
    async def get_playlist_entries_by_id(self, id: str) -> list[dict]:
        """
        Get the tracks from a playlist by its ID from Spotify. In case of
        multiple IDs, the function will return an array.

        NOTE: This function is not implemented completely yet. It assumes that
        the maximum number of tracks in a playlist does not exceed 50.
        """

        # Check if the bearer token is expired or even exists. This is required
        # for all API calls.
        if self.__token_expired():
            await self.__set_token()

        # Example API call (replace with actual implementation)
        r = await self._client.get(
            f"/v1/playlists/{id}/tracks",
            # params={"limit": 50},  # Default limit is 50 for now
            headers={"Authorization": f"Bearer {self.__bearer_token}"}
        )

        r.raise_for_status()
        return r.json()["items"]

    @classmethod
    async def get_spotify_curated_playlists(self, next: str | None = None, limit: int = 50) -> dict:
        """
        Get the playlists of the user `spotify`. Essentially, this is the
        same as the Spotify curated playlists. The user `spotify` is the
        official Spotify account.

        A sample response will have the following JSON structure:
        ```
        {
            "href": "https://api.spotify.com/v1/users/spotify/playlists?offset=0&limit=10&locale=en-US,en;q%3D0.9,ru;q%3D0.8",
            "limit": 10,
            "next": "https://api.spotify.com/v1/users/spotify/playlists?offset=10&limit=10&locale=en-US,en;q%3D0.9,ru;q%3D0.8",
            "offset": 0,
            "previous": null,
            "total": 348,
            "items": [
                    {
                    "collaborative": false,
                    "description": "All songs about drinking, cheating, heartaches and everything else going on in a classic honky tonk.",
                    "external_urls": {
                        "spotify": "https://open.spotify.com/playlist/0NfjMqrzcGKVsbYZmhf4Md"
                    },
                    "href": "https://api.spotify.com/v1/playlists/0NfjMqrzcGKVsbYZmhf4Md",
                    "id": "0NfjMqrzcGKVsbYZmhf4Md",
                    "images": [
                        {
                        "height": null,
                        "url": "https://image-cdn-ak.spotifycdn.com/image/ab67706c0000da8430ec0eff4844b5161b5075b0",
                        "width": null
                        }
                    ],
                    "name": "Classic Honky Tonk",
                    "owner": {
                        "display_name": "Spotify",
                        "external_urls": {
                        "spotify": "https://open.spotify.com/user/spotify"
                        },
                        "href": "https://api.spotify.com/v1/users/spotify",
                        "id": "spotify",
                        "type": "user",
                        "uri": "spotify:user:spotify"
                    },
                    "primary_color": null,
                    "public": true,
                    "snapshot_id": "AAAAC/9fnrEKWUIXFE/48FUgTppvFjnb",
                    "tracks": {
                        "href": "https://api.spotify.com/v1/playlists/0NfjMqrzcGKVsbYZmhf4Md/tracks",
                        "total": 50
                    },
                    "type": "playlist",
                    "uri": "spotify:playlist:0NfjMqrzcGKVsbYZmhf4Md"
                    }
            ]
        """

        # Check if the bearer token is expired or even exists. This is required
        # for all API calls.
        if self.__token_expired():
            await self.__set_token()

        # Set the target URL for the API call. If `next` is provided, use it
        # to get the next page of results. Otherwise, use the default URL.
        #
        # NOTE: We cannot get algorithmically-generated or curated playlists
        # from Spotify/authored by spotify. Hence, we must find some other user
        # to get the playlists from whose playlists include mainstream music.
        # See:
        # - https://developer.spotify.com/blog/2024-11-27-changes-to-the-web-api
        # - https://community.spotify.com/t5/Spotify-for-Developers/Using-API-Can-t-get-playlists/td-p/6612714
        # target_url = "/v1/users/spotify/playlists"
        target_url = "/v1/users/holgerchristoph/playlists"
        if next is not None:
            target_url = urllib.parse.urlparse(next).path
            target_url += "?" + urllib.parse.urlparse(next).query

        # Example API call (replace with actual implementation)
        r = await self._client.get(
            target_url,
            params={"limit": limit},
            headers={"Authorization": f"Bearer {self.__bearer_token}"}
        )

        r.raise_for_status()
        return r.json()

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
