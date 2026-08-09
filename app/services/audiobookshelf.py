import httpx

from app.config import get_settings


class AudiobookshelfClient:
    """Client for importing an author list from a self-hosted Audiobookshelf instance."""

    def __init__(self) -> None:
        self._settings = get_settings()

    async def list_authors(self) -> list[dict]:
        if not self._settings.audiobookshelf_url or not self._settings.audiobookshelf_api_token:
            raise RuntimeError("Audiobookshelf is not configured")

        headers = {"Authorization": f"Bearer {self._settings.audiobookshelf_api_token}"}
        url = f"{self._settings.audiobookshelf_url.rstrip('/')}/api/authors"

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

        return response.json().get("authors", [])
