import logging

import httpx
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Author
from app.models.enums import AuthorSource
from app.services.subscriptions import subscribe_all_users_to_author

logger = logging.getLogger(__name__)


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


async def import_authors(db: Session) -> list[Author]:
    """Pull the author list from Audiobookshelf and create rows for any not seen yet.

    Shared by the ``/audiobookshelf/import-authors`` endpoint and the scheduled
    author-import job. Raises ``RuntimeError`` if Audiobookshelf is not configured.
    """
    client = AudiobookshelfClient()
    remote_authors = await client.list_authors()

    imported: list[Author] = []
    for remote in remote_authors:
        abs_id = remote.get("id")
        existing = db.query(Author).filter(Author.audiobookshelf_author_id == abs_id).first()
        if existing is not None:
            continue

        author = Author(
            name=remote.get("name", "Unknown author"),
            source=AuthorSource.AUDIOBOOKSHELF,
            audiobookshelf_author_id=abs_id,
        )
        db.add(author)
        imported.append(author)

    db.commit()
    for author in imported:
        db.refresh(author)
        subscribe_all_users_to_author(db, author)

    return imported
