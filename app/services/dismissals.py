"""Books the user has stopped monitoring. See ``app.models.dismissal.DismissedBook``."""

from sqlalchemy.orm import Session

from app.models import Book, DismissedBook


def edition_key(book: Book) -> tuple[int, str]:
    """(author, normalized title): groups the editions of one book. Used both to collapse
    editions for display and to match dismissals."""
    return book.author_id, book.title.strip().lower()


def dismissed_keys(db: Session) -> set[tuple[int, str]]:
    return {(d.author_id, d.title_key) for d in db.query(DismissedBook)}


def is_dismissed(db: Session, book: Book) -> bool:
    author_id, title_key = edition_key(book)
    return (
        db.query(DismissedBook)
        .filter(DismissedBook.author_id == author_id, DismissedBook.title_key == title_key)
        .first()
        is not None
    )


def dismiss_book(db: Session, book: Book) -> None:
    """Stop monitoring every edition of ``book``. Idempotent."""
    if is_dismissed(db, book):
        return
    author_id, title_key = edition_key(book)
    db.add(DismissedBook(author_id=author_id, title_key=title_key, title=book.title))
    db.commit()


def restore_book(db: Session, book: Book) -> None:
    """Resume monitoring ``book`` (and its other editions). Idempotent."""
    author_id, title_key = edition_key(book)
    db.query(DismissedBook).filter(
        DismissedBook.author_id == author_id, DismissedBook.title_key == title_key
    ).delete()
    db.commit()
