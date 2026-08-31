"""Response models for the external integration API (`/api/v1`).

These are a deliberately stable, self-contained view of the catalog: each release carries
its author's name and a pre-computed `days_until` so a consumer (e.g. a homepage dashboard
widget) never has to join against `/authors` or do date math itself.
"""

from datetime import date, datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel

from app.models.enums import BookFormat, BookStatus
from app.utils.dates import derive_book_status

if TYPE_CHECKING:
    from app.models import Book


class ReleaseItem(BaseModel):
    id: int
    title: str
    author: str
    format: BookFormat
    status: BookStatus
    release_date: date | None
    announced_date: date | None
    days_until: int | None
    series: str | None
    series_sequence: str | None
    cover_url: str | None
    source: str

    @classmethod
    def from_book(cls, book: "Book", today: date) -> "ReleaseItem":
        days_until: int | None = None
        if book.release_date is not None and book.release_date >= today:
            days_until = (book.release_date - today).days
        return cls(
            id=book.id,
            title=book.title,
            author=book.author.name,
            format=book.format,
            status=derive_book_status(book.release_date, today),
            release_date=book.release_date,
            announced_date=book.announced_date,
            days_until=days_until,
            series=book.series,
            series_sequence=book.series_sequence,
            cover_url=book.cover_url,
            source=book.source,
        )


class UpcomingReleasesResponse(BaseModel):
    generated_at: datetime
    count: int
    releases: list[ReleaseItem]


class CalendarSection(BaseModel):
    label: str
    releases: list[ReleaseItem]


class ReleaseCalendarResponse(BaseModel):
    generated_at: datetime
    sections: list[CalendarSection]


class IntegrationStatsResponse(BaseModel):
    generated_at: datetime
    authors_tracked: int
    upcoming_count: int
    next_release: ReleaseItem | None
