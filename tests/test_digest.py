from datetime import date

from app.models import Book
from app.models.enums import BookFormat
from app.services.digest import bucket_books


def _book(title: str, release_date: date | None) -> Book:
    return Book(
        title=title, format=BookFormat.AUDIOBOOK, source="manual", release_date=release_date
    )


def test_bucket_books_groups_by_month_then_quarter_then_tba():
    today = date(2026, 8, 15)
    books = [
        _book("this month", date(2026, 8, 20)),
        _book("next month", date(2026, 9, 5)),
        _book("month three", date(2026, 10, 1)),
        _book("next quarter", date(2026, 11, 30)),
        _book("far quarter", date(2027, 2, 1)),
        _book("no date", None),
    ]

    buckets, full_detail_labels = bucket_books(books, today=today)

    assert list(buckets.keys()) == [
        "This month",
        "September 2026",
        "October 2026",
        "Q4 2026",
        "Q1 2027",
        "Date TBA",
    ]
    assert [b.title for b in buckets["This month"]] == ["this month"]
    assert [b.title for b in buckets["September 2026"]] == ["next month"]
    assert [b.title for b in buckets["October 2026"]] == ["month three"]
    assert [b.title for b in buckets["Q4 2026"]] == ["next quarter"]
    assert [b.title for b in buckets["Q1 2027"]] == ["far quarter"]
    assert [b.title for b in buckets["Date TBA"]] == ["no date"]

    # Only this month and next month get full per-book detail (e.g. cover art);
    # everything further out is a compact grouped list.
    assert full_detail_labels == {"This month", "September 2026"}


def test_bucket_books_tba_is_always_last_regardless_of_input_order():
    today = date(2026, 8, 15)
    books = [
        _book("no date", None),
        _book("this month", date(2026, 8, 20)),
    ]

    buckets, _ = bucket_books(books, today=today)

    assert list(buckets.keys()) == ["This month", "Date TBA"]


def test_bucket_books_no_book_appears_in_more_than_one_bucket():
    today = date(2026, 8, 15)
    books = [_book(f"book {i}", date(2026, 9, 1)) for i in range(3)]

    buckets, _ = bucket_books(books, today=today)

    total = sum(len(group) for group in buckets.values())
    assert total == len(books)
    assert len(buckets) == 1
