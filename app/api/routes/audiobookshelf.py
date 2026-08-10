from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Author
from app.models.enums import AuthorSource
from app.schemas.author import AuthorRead
from app.services.audiobookshelf import AudiobookshelfClient
from app.services.subscriptions import subscribe_all_users_to_author

router = APIRouter(prefix="/audiobookshelf", tags=["audiobookshelf"])


@router.post("/import-authors", response_model=list[AuthorRead])
async def import_authors(db: Session = Depends(get_db)) -> list[Author]:
    client = AudiobookshelfClient()
    try:
        remote_authors = await client.list_authors()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

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
