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
            "products_sort_by": "ReleaseDate",
            "response_groups": "product_desc,product_attrs,media",
        }

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(self._base_url, params=params)
            response.raise_for_status()

        return response.json().get("products", [])
