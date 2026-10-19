"""iCalendar (RFC 5545) feed of release dates, served at ``/api/v1/releases.ics``.

Calendar apps subscribe to the URL and re-fetch it on their own schedule, so each release
is an all-day event on its release date. Hand-rolled rather than pulling in an iCalendar
library: the output is a handful of properties per event, and the only subtle parts are
text escaping and line folding.
"""

import hashlib
from datetime import date, datetime, timedelta
from urllib.parse import quote

from app.models import Book
from app.models.enums import BookFormat
from app.services.dismissals import edition_key

_FORMAT_LABEL = {BookFormat.BOOK: "Book", BookFormat.AUDIOBOOK: "Audiobook"}

# Hint for how often clients should re-fetch; most honour one of the two properties.
_REFRESH_INTERVAL = "PT6H"


def goodreads_search_url(title: str, author: str | None) -> str:
    """Goodreads has no ID we can derive from an Audible ASIN or Google Books ID, so link
    to a title + author search (same as the web UI)."""
    query = " ".join(part for part in (title, author) if part)
    return "https://www.goodreads.com/search?q=" + quote(query)


def _escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
    )


def _fold(line: str) -> str:
    """Splits a content line into 75-octet chunks, continuation lines starting with a space,
    without cutting a multi-byte UTF-8 character in half."""
    out: list[str] = []
    current = ""
    limit = 75
    for char in line:
        if len((current + char).encode()) > limit:
            out.append(current)
            current = " " + char
            limit = 75
        else:
            current += char
    out.append(current)
    return "\r\n".join(out)


def _uid(book: Book) -> str:
    """Stable per title rather than per row, so collapsing a different edition of the same
    book (or re-ingesting it) updates the existing event instead of adding a second one."""
    author_id, title_key = edition_key(book)
    digest = hashlib.sha1(title_key.encode()).hexdigest()[:16]
    return f"book-{author_id}-{digest}@bookdrop"


def _event(book: Book, release_date: date, stamp: str) -> list[str]:
    author = book.author.name
    link = goodreads_search_url(book.title, author)

    details: list[str] = []
    if book.series:
        details.append(book.series + (f" #{book.series_sequence}" if book.series_sequence else ""))
    details.append(f"{_FORMAT_LABEL.get(book.format, book.format)} by {author}")
    details.append(f"Goodreads: {link}")

    lines = [
        "BEGIN:VEVENT",
        f"UID:{_uid(book)}",
        f"DTSTAMP:{stamp}",
        f"DTSTART;VALUE=DATE:{release_date:%Y%m%d}",
        f"DTEND;VALUE=DATE:{release_date + timedelta(days=1):%Y%m%d}",
        f"SUMMARY:{_escape(f'{book.title} — {author}')}",
        f"DESCRIPTION:{_escape(chr(10).join(details))}",
        f"URL:{link}",
        "TRANSP:TRANSPARENT",
    ]
    if book.cover_url:
        lines.append(f"IMAGE;VALUE=URI;DISPLAY=BADGE:{book.cover_url}")
    lines.append("END:VEVENT")
    return lines


def build_release_calendar(books: list[Book], now: datetime) -> str:
    """Renders dated ``books`` as an iCalendar document. Undated ("Date TBA") titles have
    nowhere to go on a calendar and are skipped. ``now`` is naive UTC."""
    stamp = f"{now:%Y%m%dT%H%M%S}Z"
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Bookdrop//Release calendar//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Bookdrop releases",
        "X-WR-CALDESC:Release dates for books from the authors you follow",
        f"REFRESH-INTERVAL;VALUE=DURATION:{_REFRESH_INTERVAL}",
        f"X-PUBLISHED-TTL:{_REFRESH_INTERVAL}",
    ]
    for book in books:
        if book.release_date is not None:
            lines.extend(_event(book, book.release_date, stamp))
    lines.append("END:VCALENDAR")
    return "".join(_fold(line) + "\r\n" for line in lines)
