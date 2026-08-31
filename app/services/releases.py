"""Read-only queries over the tracked catalog, shared by the web UI's `/books` route and
the external integration API (`app/api/routes/integration.py`)."""

from datetime import date, timedelta

from sqlalchemy.orm import Session, joinedload

from app.models import Author, Book
from app.models.enums import BookFormat


def upcoming_releases(
    db: Session,
    *,
    within_days: int | None = None,
    formats: list[BookFormat] | None = None,
    include_undated: bool = True,
    limit: int | None = None,
    today: date | None = None,
) -> list[Book]:
    """Books that haven't been released yet, across every tracked author.

    - `within_days` caps how far into the future dated releases may be.
    - `include_undated` keeps announced-but-no-date ("Date TBA") titles in the result;
      these are always sorted last and are unaffected by `within_days`.
    - Multiple editions of the same title (e.g. an Audible and a Google Books row) are
      collapsed to one, matching the web UI and the digest.
    """
    today = today or date.today()

    dated = Book.release_date >= today
    if within_days is not None:
        dated = dated & (Book.release_date <= today + timedelta(days=within_days))
    date_filter = dated | Book.release_date.is_(None) if include_undated else dated

    query = db.query(Book).options(joinedload(Book.author)).filter(date_filter)
    if formats:
        query = query.filter(Book.format.in_(formats))

    books = query.order_by(Book.release_date.asc()).all()

    deduped: dict[tuple[int, str], Book] = {}
    for book in books:
        key = (book.author_id, book.title.strip().lower())
        deduped.setdefault(key, book)

    result = list(deduped.values())
    # SQLite orders NULLs first on ASC; force undated releases to the end instead.
    result.sort(key=lambda b: (b.release_date is None, b.release_date or date.max))

    return result[:limit] if limit is not None else result


def tracked_author_count(db: Session) -> int:
    return db.query(Author).count()
