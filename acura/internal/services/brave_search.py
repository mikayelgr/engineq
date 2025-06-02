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
