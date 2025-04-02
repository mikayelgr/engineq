import httpx
from dataclasses import dataclass
from internal.conf import Config


@dataclass
class BraveSearchService:
    client = httpx.AsyncClient(
        base_url="https://api.search.brave.com",
        follow_redirects=True,
        headers={"Accept": "application/json"})

    async def search_youtube(self, query: str, num_results: int = 2):
        query = "site:youtube.com" + ' ' + query
        search_response = await self.client.get("/res/v1/web/search", params={
            "q": query,
            "country": "US",  # for now this will remain as the default
            "ui-lang": "en-US",
            "count": num_results,
            "safesearch": "strict",
            "text_decorations": False,
        }, headers={"X-Subscription-Token": Config().BRAVE_SEARCH_TOKEN})

        search_response.raise_for_status()
        search_response_dict = search_response.json()
        if ("web" not in search_response_dict) or (len(search_response_dict["web"]["results"]) == 0):
            return None

        return search_response_dict["web"]["results"]
