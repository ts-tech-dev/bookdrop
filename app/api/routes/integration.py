"""Versioned, read-only API for other services to pull release data from Bookdrop.

Kept separate from the internal resource routers so the shape can stay stable for external
consumers. When `BOOKDROP_INTEGRATION_API_TOKEN` is set, every endpoint here requires it
via `Authorization: Bearer <token>`, an `X-API-Key` header, or a `token` query parameter
(calendar apps subscribing to `releases.ics` can't send headers); otherwise the API is
open (the common single-user homelab case). CORS is configured in `app/main.py`.
"""

from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.enums import BookFormat
from app.schemas.integration import (
    CalendarSection,
    IntegrationStatsResponse,
    ReleaseCalendarResponse,
    ReleaseItem,
    UpcomingReleasesResponse,
)
from app.services.calendar_feed import build_release_calendar
from app.services.digest import bucket_books
from app.services.releases import tracked_author_count, upcoming_releases
from app.utils.time import utcnow


def verify_api_token(
    authorization: Annotated[str | None, Header()] = None,
    x_api_key: Annotated[str | None, Header()] = None,
    token: Annotated[str | None, Query(include_in_schema=False)] = None,
) -> None:
    expected = get_settings().integration_api_token
    if not expected:
        return

    presented = x_api_key or token
    if authorization and authorization.lower().startswith("bearer "):
        presented = authorization[len("bearer ") :].strip()

    if presented != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API token",
            headers={"WWW-Authenticate": "Bearer"},
        )


router = APIRouter(
    prefix="/api/v1",
    tags=["integration"],
    dependencies=[Depends(verify_api_token)],
)

WithinDays = Annotated[int | None, Query(ge=1, le=1825)]
FormatFilter = Annotated[BookFormat | None, Query(alias="format")]


@router.get("/releases/upcoming", response_model=UpcomingReleasesResponse)
def get_upcoming_releases(
    db: Session = Depends(get_db),
    within_days: WithinDays = None,
    book_format: FormatFilter = None,
    include_undated: bool = Query(default=True),
    limit: Annotated[int | None, Query(ge=1, le=500)] = None,
) -> UpcomingReleasesResponse:
    today = date.today()
    books = upcoming_releases(
        db,
        within_days=within_days,
        formats=[book_format] if book_format else None,
        include_undated=include_undated,
        limit=limit,
        today=today,
    )
    releases = [ReleaseItem.from_book(book, today) for book in books]
    return UpcomingReleasesResponse(generated_at=utcnow(), count=len(releases), releases=releases)


@router.get("/releases/calendar", response_model=ReleaseCalendarResponse)
def get_release_calendar(
    db: Session = Depends(get_db),
    within_days: WithinDays = None,
    book_format: FormatFilter = None,
) -> ReleaseCalendarResponse:
    today = date.today()
    books = upcoming_releases(
        db,
        within_days=within_days,
        formats=[book_format] if book_format else None,
        today=today,
    )
    buckets, _ = bucket_books(books, today=today)
    sections = [
        CalendarSection(
            label=label,
            releases=[ReleaseItem.from_book(book, today) for book in bucket],
        )
        for label, bucket in buckets.items()
    ]
    return ReleaseCalendarResponse(generated_at=utcnow(), sections=sections)


@router.get(
    "/releases.ics",
    response_class=Response,
    responses={200: {"content": {"text/calendar": {}}}},
)
def get_release_ics(
    db: Session = Depends(get_db),
    book_format: FormatFilter = None,
    past_days: Annotated[int, Query(ge=0, le=365)] = 30,
) -> Response:
    """Subscribable iCalendar feed: one all-day event per release, from `past_days` ago
    onwards, so a release stays on the calendar for a while after it lands."""
    today = date.today()
    books = upcoming_releases(
        db,
        formats=[book_format] if book_format else None,
        include_undated=False,
        today=today,
        since=today - timedelta(days=past_days),
    )
    return Response(
        content=build_release_calendar(books, now=utcnow()),
        media_type="text/calendar; charset=utf-8",
        headers={"Content-Disposition": 'inline; filename="bookdrop.ics"'},
    )


@router.get("/stats", response_model=IntegrationStatsResponse)
def get_stats(db: Session = Depends(get_db)) -> IntegrationStatsResponse:
    today = date.today()
    books = upcoming_releases(db, today=today)
    dated = [book for book in books if book.release_date is not None]
    return IntegrationStatsResponse(
        generated_at=utcnow(),
        authors_tracked=tracked_author_count(db),
        upcoming_count=len(books),
        next_release=ReleaseItem.from_book(dated[0], today) if dated else None,
    )
