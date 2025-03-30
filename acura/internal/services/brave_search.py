import httpx
from dataclasses import dataclass
import logging
from internal.conf import Config

logger = logging.getLogger(__name__)
client = httpx.AsyncClient(base_url="https://api.search.brave.com", follow_redirects=True, headers={
    "Accept": "application/json",
})


@dataclass
class BraveSearchService:
    async def search_youtube(query: str, num_results: int = 2) -> dict | None:
        try:
            query = "site:youtube.com" + ' ' + query
            search_response = await client.get("/res/v1/web/search", params={
                "q": query,
                "country": "US",  # for now this will remain as the default
                "ui-lang": "en-US",
                "count": num_results,
                "safesearch": "strict",
                "text_decorations": False,
            }, headers={"X-Subscription-Token": Config().BRAVE_SEARCH_TOKEN})

            if search_response.status_code in (302, 200):
                search_response_dict = search_response.json()
                if ("web" not in search_response_dict) or (len(search_response_dict["web"]["results"]) == 0):
                    return None

                return search_response_dict["web"]["results"]

            return None
        except Exception as e:
            logger.error(e)
            return None
