from datetime import date, datetime

from app.models.enums import BookStatus


def derive_book_status(release_date: date | None, today: date | None = None) -> BookStatus:
    """The real status of a book, derived from its release date.

    Ingest always writes ``status = ANNOUNCED`` and never revisits it, so a title whose
    release date has since passed still sits in the DB as ``ANNOUNCED``. Callers that
    surface status to a user (the web shelf, the integration API) resolve it through here
    instead of trusting the column: a book is ``RELEASED`` once its release date is today
    or earlier, and stays ``ANNOUNCED`` while undated or still in the future.
    """
    if release_date is None:
        return BookStatus.ANNOUNCED
    return BookStatus.RELEASED if release_date <= (today or date.today()) else BookStatus.ANNOUNCED


def parse_date(value: str | None) -> date | None:
    """Best-effort parse of the loose date formats returned by Audible/Google Books."""
    if not value:
        return None

    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    return None
