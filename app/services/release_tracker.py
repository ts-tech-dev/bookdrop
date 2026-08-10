import logging

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Author, Book
from app.models.enums import BookFormat, BookStatus
from app.services.audible import AudibleClient
from app.services.google_books import GoogleBooksClient
from app.services.notifier import Notifier
from app.utils.dates import parse_date

logger = logging.getLogger(__name__)


def _is_english(language: str | None) -> bool:
    """True for English or unlabeled editions; Audible uses "english", Google Books "en"."""
    if language is None:
        return True
    return language.strip().lower().startswith("en")


def _extract_series(product: dict) -> tuple[str | None, str | None]:
    """Audible's "series" response group is a list; a book usually belongs to just one."""
    series_list = product.get("series") or []
    if not series_list:
        return None, None
    first = series_list[0]
    return first.get("title"), first.get("sequence")


def _has_other_edition(db: Session, book: Book) -> bool:
    """True if another Book row already exists for this author with the same title.

    Audible and Google Books frequently surface the same underlying book (different
    translations, box sets, or one from each source); this prevents notifying once per
    edition when only the first-seen edition should trigger a notification.
    """
    return (
        db.query(Book)
        .filter(
            Book.author_id == book.author_id,
            Book.id != book.id,
            func.lower(func.trim(Book.title)) == book.title.strip().lower(),
        )
        .first()
        is not None
    )


async def check_for_new_releases(db: Session) -> None:
    """Polls Audible and Google Books for every tracked author and notifies new titles."""
    audible = AudibleClient()
    google_books = GoogleBooksClient()
    notifier = Notifier(db)

    authors = db.query(Author).all()
    logger.info("Checking for new releases across %d authors", len(authors))

    for author in authors:
        try:
            products = await audible.search_by_author(author.name)
        except Exception:
            logger.exception("Audible lookup failed for author %r", author.name)
            products = []

        for product in products:
            book = _upsert_audible_book(db, author, product)
            if book is not None:
                logger.info("New Audible title for %r: %r", author.name, book.title)
                if not _has_other_edition(db, book):
                    await notifier.notify_for_book(book)

        try:
            volumes = await google_books.search_by_author(author.name)
        except Exception:
            logger.exception("Google Books lookup failed for author %r", author.name)
            volumes = []

        for volume in volumes:
            book = _upsert_google_books_book(db, author, volume)
            if book is not None:
                logger.info("New Google Books title for %r: %r", author.name, book.title)
                if not _has_other_edition(db, book):
                    await notifier.notify_for_book(book)

    logger.info("Release check complete")


def _upsert_audible_book(db: Session, author: Author, product: dict) -> Book | None:
    external_id = product.get("asin")
    if external_id is None:
        return None

    if not _is_english(product.get("language")):
        return None

    existing = (
        db.query(Book).filter(Book.source == "audible", Book.external_id == external_id).first()
    )
    if existing is not None:
        return None

    series, series_sequence = _extract_series(product)
    book = Book(
        author_id=author.id,
        title=product.get("title", "Unknown title"),
        format=BookFormat.AUDIOBOOK,
        status=BookStatus.ANNOUNCED,
        release_date=parse_date(product.get("release_date")),
        source="audible",
        external_id=external_id,
        cover_url=(product.get("product_images") or {}).get("500"),
        series=series,
        series_sequence=series_sequence,
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def _upsert_google_books_book(db: Session, author: Author, volume: dict) -> Book | None:
    external_id = volume.get("id")
    if external_id is None:
        return None

    info = volume.get("volumeInfo", {})
    if not _is_english(info.get("language")):
        return None

    existing = (
        db.query(Book)
        .filter(Book.source == "google_books", Book.external_id == external_id)
        .first()
    )
    if existing is not None:
        return None

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
