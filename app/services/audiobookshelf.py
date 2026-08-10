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
        base_url = self._settings.audiobookshelf_url.rstrip("/")

        async with httpx.AsyncClient(timeout=15) as client:
            libraries_response = await client.get(f"{base_url}/api/libraries", headers=headers)
            libraries_response.raise_for_status()
            library_ids = [
                library["id"] for library in libraries_response.json().get("libraries", [])
            ]

            authors: list[dict] = []
            for library_id in library_ids:
                response = await client.get(
                    f"{base_url}/api/libraries/{library_id}/authors", headers=headers
                )
                response.raise_for_status()
                authors.extend(response.json().get("authors", []))

        return authors
