from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Book
from app.schemas.book import BookRead
from app.services.dismissals import dismiss_book, dismissed_keys, edition_key, restore_book

router = APIRouter(prefix="/books", tags=["books"])

# Books released before this cutoff are old backlog, not a "new release" worth showing.
_MAX_RELEASE_AGE = timedelta(days=120)


@router.get("", response_model=list[BookRead])
def list_books(include_dismissed: bool = False, db: Session = Depends(get_db)) -> list[BookRead]:
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
        deduped.setdefault(edition_key(book), book)

    dismissed = dismissed_keys(db)
    return [
        BookRead.model_validate(book).model_copy(update={"dismissed": key in dismissed})
        for key, book in deduped.items()
        if include_dismissed or key not in dismissed
    ]


def _get_book(db: Session, book_id: int) -> Book:
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.post("/{book_id}/dismiss", status_code=204)
def dismiss(book_id: int, db: Session = Depends(get_db)) -> None:
    """Stop monitoring a book (all of its editions): no more notifications, and it's
    hidden from the shelf, the digest and the integration API."""
    dismiss_book(db, _get_book(db, book_id))


@router.delete("/{book_id}/dismiss", status_code=204)
def restore(book_id: int, db: Session = Depends(get_db)) -> None:
    restore_book(db, _get_book(db, book_id))
