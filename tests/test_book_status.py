from datetime import date, timedelta

import pytest

from app.models import Author, Book
from app.models.enums import BookFormat, BookStatus
from app.utils.dates import derive_book_status

TODAY = date(2026, 8, 31)


@pytest.mark.parametrize(
    ("release_date", "expected"),
    [
        (None, BookStatus.ANNOUNCED),
        (TODAY + timedelta(days=1), BookStatus.ANNOUNCED),
        (TODAY, BookStatus.RELEASED),
        (TODAY - timedelta(days=1), BookStatus.RELEASED),
        (TODAY - timedelta(days=3650), BookStatus.RELEASED),
    ],
)
def test_derive_book_status(release_date, expected):
    assert derive_book_status(release_date, today=TODAY) is expected


@pytest.fixture()
def noni(db_session):
    author = Author(name="Lynette Noni")
    db_session.add(author)
    db_session.flush()
    today = date.today()
    db_session.add_all(
        [
            Book(
                author_id=author.id,
                title="Shadow Reaper",  # shipped weeks ago, but ingest left it ANNOUNCED
                format=BookFormat.AUDIOBOOK,
                status=BookStatus.ANNOUNCED,
                release_date=today - timedelta(days=30),
                source="audible",
            ),
            Book(
                author_id=author.id,
                title="The Next One",
                format=BookFormat.AUDIOBOOK,
                status=BookStatus.ANNOUNCED,
                release_date=today + timedelta(days=30),
                source="audible",
            ),
            Book(
                author_id=author.id,
                title="Untitled",
                format=BookFormat.AUDIOBOOK,
                status=BookStatus.ANNOUNCED,
                release_date=None,
                source="audible",
            ),
        ]
    )
    db_session.commit()
    return author


def test_books_endpoint_reports_released_for_past_dates(client, noni):
    by_title = {b["title"]: b for b in client.get("/books").json()}

    assert by_title["Shadow Reaper"]["status"] == "released"
    assert by_title["The Next One"]["status"] == "announced"
    assert by_title["Untitled"]["status"] == "announced"


def test_integration_api_reports_released_for_today(client, db_session):
    author = Author(name="Someone")
    db_session.add(author)
    db_session.flush()
    db_session.add(
        Book(
            author_id=author.id,
            title="Lands Today",
            format=BookFormat.BOOK,
            status=BookStatus.ANNOUNCED,
            release_date=date.today(),
            source="google_books",
        )
    )
    db_session.commit()

    item = next(
        r
        for r in client.get("/api/v1/releases/upcoming").json()["releases"]
        if r["title"] == "Lands Today"
    )
    assert item["status"] == "released"
    assert item["days_until"] == 0
