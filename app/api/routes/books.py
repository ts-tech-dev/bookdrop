from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Book
from app.schemas.book import BookRead

router = APIRouter(prefix="/books", tags=["books"])

# Books released before this cutoff are old backlog, not a "new release" worth showing.
_MAX_RELEASE_AGE = timedelta(days=120)


@router.get("", response_model=list[BookRead])
def list_books(db: Session = Depends(get_db)) -> list[Book]:
    cutoff = date.today() - _MAX_RELEASE_AGE
    books = (
        db.query(Book)
        .filter((Book.release_date.is_(None)) | (Book.release_date >= cutoff))
        .order_by(Book.release_date.asc())
        .all()
    )

    # Collapse multiple editions (different source/format, same title) of the same book.
    deduped: dict[tuple[int, str], Book] = {}
    for book in books:
        key = (book.author_id, book.title.strip().lower())
        deduped.setdefault(key, book)

    return list(deduped.values())
