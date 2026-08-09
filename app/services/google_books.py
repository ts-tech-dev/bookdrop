import httpx

from app.config import get_settings

GOOGLE_BOOKS_API_URL = "https://www.googleapis.com/books/v1/volumes"


class GoogleBooksClient:
    """Looks up new/upcoming titles for an author via the Google Books API."""

    def __init__(self) -> None:
        self._settings = get_settings()

    async def search_by_author(self, author_name: str) -> list[dict]:
        params: dict[str, str | int] = {
            "q": f'inauthor:"{author_name}"',
            "orderBy": "newest",
            "maxResults": 40,
        }
        if self._settings.google_books_api_key:
            params["key"] = self._settings.google_books_api_key

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(GOOGLE_BOOKS_API_URL, params=params)
            response.raise_for_status()

        return response.json().get("items", [])
