import httpx

from app.config import get_settings

_MARKETPLACE_HOSTS = {
    "us": "api.audible.com",
    "uk": "api.audible.co.uk",
    "de": "api.audible.de",
    "fr": "api.audible.fr",
    "ca": "api.audible.ca",
    "au": "api.audible.com.au",
}


class AudibleClient:
    """Thin client around Audible's unofficial catalog API, used to spot new audiobooks."""

    def __init__(self) -> None:
        self._settings = get_settings()

    @property
    def _base_url(self) -> str:
        host = _MARKETPLACE_HOSTS.get(self._settings.audible_marketplace, _MARKETPLACE_HOSTS["us"])
        return f"https://{host}/1.0/catalog/products"

    async def search_by_author(self, author_name: str) -> list[dict]:
        params: dict[str, str | int] = {
            "author": author_name,
            "num_results": 50,
            # Newest first ("-" prefix = descending). This request isn't paginated, so an
            # author with a large back catalogue (main series + dramatized adaptations +
            # translations) would otherwise fill all 50 slots with old titles and the
            # release checker would never see anything new.
            "products_sort_by": "-ReleaseDate",
            "response_groups": "product_desc,product_attrs,media,series",
        }

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(self._base_url, params=params)
            response.raise_for_status()

        return response.json().get("products", [])

    async def get_product(self, asin: str) -> dict | None:
        params = {"response_groups": "product_desc,product_attrs,series"}

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(f"{self._base_url}/{asin}", params=params)
            if response.status_code == 404:
                return None
            response.raise_for_status()

        return response.json().get("product")

    async def similar_products(
        self, asin: str, similarity_type: str, num_results: int = 20
    ) -> list[dict]:
        """Audible's "listeners also enjoyed" style lookup for a single title.

        ``similarity_type`` is one of Audible's ``RawSimilarities``, ``InTheSameSeries``,
        ``ByTheSameAuthor`` or ``ByTheSameNarrator``. Audible caps ``num_results`` at 50.
        """
        params: dict[str, str | int] = {
            "similarity_type": similarity_type,
            "num_results": min(num_results, 50),
            "response_groups": "product_desc,product_attrs,media,series,contributors",
        }

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(f"{self._base_url}/{asin}/sims", params=params)
            response.raise_for_status()

        return response.json().get("similar_products", [])

    def product_url(self, asin: str) -> str:
        """The public store page for a title, on the configured marketplace's site."""
        host = _MARKETPLACE_HOSTS.get(self._settings.audible_marketplace, _MARKETPLACE_HOSTS["us"])
        return f"https://{host.replace('api.', 'www.', 1)}/pd/{asin}"
