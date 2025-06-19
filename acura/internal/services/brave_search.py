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

import httpx
import asyncio
from dataclasses import dataclass
from internal.conf import Config
import logging

logging.getLogger("httpx").setLevel(logging.CRITICAL + 1)


@dataclass
class BraveSearchService:
    _client = httpx.AsyncClient(
        base_url="https://api.search.brave.com",
        follow_redirects=True,
        headers={"Accept": "application/json"})

    @classmethod
    async def _make_request(cls, endpoint: str, params: dict, headers: dict | None = None, max_retries: int = 5):
        retries = 0
        backoff = 1  # Initial backoff in seconds

        while retries < max_retries:
            try:
                response = await cls._client.get(endpoint, params=params, headers=headers)

                if response.status_code == 429:
                    retries += 1
                    await asyncio.sleep(backoff)
                    backoff *= 2  # Exponential backoff
                    continue

                response.raise_for_status()
                return response.json()

            except httpx.RequestError as e:
                retries += 1
                await asyncio.sleep(backoff)
                backoff *= 2  # Exponential backoff
                if retries >= max_retries:
                    raise e

        raise Exception(
            "Max retries exceeded while trying to perform the request.")

    @classmethod
    async def search_youtube_for_videos(cls, query: str, num_results: int = 10) -> list[dict]:
        query = "site:youtube.com" + ' ' + query
        params = {
            "q": query,
            "country": "US",  # for now this will remain as the default
            "ui-lang": "en-US",
            "count": num_results,
            "safesearch": "strict",
            "text_decorations": False,
        }
        headers = {"X-Subscription-Token": Config().BRAVE_SEARCH_TOKEN}
        response_data = await cls._make_request("/res/v1/web/search", params=params, headers=headers)

        results = []
        if ("web" in response_data) and ("results" in response_data["web"]):
            results.extend(response_data["web"]["results"])
        if ("videos" in response_data) and ("results" in response_data["videos"]):
            results.extend(response_data["videos"]["results"])

        return results
