from sqlalchemy.orm import Session

from app.models import Author, Book
from app.models.enums import BookFormat, BookStatus
from app.services.audible import AudibleClient
from app.services.google_books import GoogleBooksClient
from app.services.notifier import Notifier
from app.utils.dates import parse_date


async def check_for_new_releases(db: Session) -> None:
    """Polls Audible and Google Books for every tracked author and notifies new titles."""
    audible = AudibleClient()
    google_books = GoogleBooksClient()
    notifier = Notifier(db)

    for author in db.query(Author).all():
        for product in await audible.search_by_author(author.name):
            book = _upsert_audible_book(db, author, product)
            if book is not None:
                await notifier.notify_for_book(book)

        for volume in await google_books.search_by_author(author.name):
            book = _upsert_google_books_book(db, author, volume)
            if book is not None:
                await notifier.notify_for_book(book)


def _upsert_audible_book(db: Session, author: Author, product: dict) -> Book | None:
    external_id = product.get("asin")
    if external_id is None:
        return None

    existing = (
        db.query(Book).filter(Book.source == "audible", Book.external_id == external_id).first()
    )
    if existing is not None:
        return None

    book = Book(
        author_id=author.id,
        title=product.get("title", "Unknown title"),
        format=BookFormat.AUDIOBOOK,
        status=BookStatus.ANNOUNCED,
        release_date=parse_date(product.get("release_date")),
        source="audible",
        external_id=external_id,
        cover_url=(product.get("product_images") or {}).get("500"),
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def _upsert_google_books_book(db: Session, author: Author, volume: dict) -> Book | None:
    external_id = volume.get("id")
    if external_id is None:
        return None

    existing = (
        db.query(Book)
        .filter(Book.source == "google_books", Book.external_id == external_id)
        .first()
    )
    if existing is not None:
        return None

    info = volume.get("volumeInfo", {})
    book = Book(
        author_id=author.id,
        title=info.get("title", "Unknown title"),
        format=BookFormat.BOOK,
        status=BookStatus.ANNOUNCED,
        release_date=parse_date(info.get("publishedDate")),
        source="google_books",
        external_id=external_id,
        cover_url=(info.get("imageLinks") or {}).get("thumbnail"),
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    return book
