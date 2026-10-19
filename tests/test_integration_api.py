from datetime import date, timedelta

import pytest

from app.config import get_settings
from app.models import Author, Book
from app.models.enums import BookFormat, BookStatus


@pytest.fixture()
def seeded(db_session):
    today = date.today()
    sanderson = Author(name="Brandon Sanderson")
    hobb = Author(name="Robin Hobb")
    db_session.add_all([sanderson, hobb])
    db_session.flush()

    books = [
        Book(
            author_id=sanderson.id,
            title="Wind and Truth",
            format=BookFormat.BOOK,
            status=BookStatus.ANNOUNCED,
            release_date=today + timedelta(days=10),
            source="google_books",
        ),
        Book(
            author_id=sanderson.id,
            title="Wind and Truth",  # duplicate edition, must be collapsed
            format=BookFormat.AUDIOBOOK,
            status=BookStatus.ANNOUNCED,
            release_date=today + timedelta(days=10),
            source="audible",
        ),
        Book(
            author_id=sanderson.id,
            title="Untitled Cosmere Novel",
            format=BookFormat.BOOK,
            status=BookStatus.ANNOUNCED,
            release_date=None,  # Date TBA
            source="google_books",
        ),
        Book(
            author_id=hobb.id,
            title="Far Future Audiobook",
            format=BookFormat.AUDIOBOOK,
            status=BookStatus.ANNOUNCED,
            release_date=today + timedelta(days=400),
            source="audible",
        ),
        Book(
            author_id=hobb.id,
            title="Old Backlog Title",
            format=BookFormat.BOOK,
            status=BookStatus.RELEASED,
            release_date=today - timedelta(days=30),
            source="google_books",
        ),
    ]
    db_session.add_all(books)
    db_session.commit()
    return today


def test_upcoming_releases_shape_and_filtering(client, seeded):
    resp = client.get("/api/v1/releases/upcoming")
    assert resp.status_code == 200
    body = resp.json()

    titles = [r["title"] for r in body["releases"]]
    # Past release excluded, duplicate edition collapsed, undated sorted last.
    assert titles == ["Wind and Truth", "Far Future Audiobook", "Untitled Cosmere Novel"]
    assert body["count"] == 3

    first = body["releases"][0]
    assert first["author"] == "Brandon Sanderson"
    assert first["days_until"] == 10
    assert body["releases"][-1]["days_until"] is None


def test_upcoming_releases_within_days_and_format(client, seeded):
    params = {"within_days": 30, "include_undated": False}
    resp = client.get("/api/v1/releases/upcoming", params=params)
    assert [r["title"] for r in resp.json()["releases"]] == ["Wind and Truth"]

    params = {"format": "audiobook", "include_undated": False}
    resp = client.get("/api/v1/releases/upcoming", params=params)
    releases = resp.json()["releases"]
    assert [r["title"] for r in releases] == ["Wind and Truth", "Far Future Audiobook"]
    assert {r["format"] for r in releases} == {"audiobook"}

    resp = client.get("/api/v1/releases/upcoming", params={"limit": 1})
    assert len(resp.json()["releases"]) == 1


def test_release_calendar_groups_into_sections(client, seeded):
    resp = client.get("/api/v1/releases/calendar")
    assert resp.status_code == 200
    sections = {s["label"]: [r["title"] for r in s["releases"]] for s in resp.json()["sections"]}

    assert "Untitled Cosmere Novel" in sections["Date TBA"]
    assert list(resp.json()["sections"])[-1]["label"] == "Date TBA"
    all_titles = [t for titles in sections.values() for t in titles]
    assert "Old Backlog Title" not in all_titles


def test_stats(client, seeded):
    resp = client.get("/api/v1/stats")
    assert resp.status_code == 200
    body = resp.json()
    assert body["authors_tracked"] == 2
    assert body["upcoming_count"] == 3
    assert body["next_release"]["title"] == "Wind and Truth"


def test_token_required_when_configured(client, seeded, monkeypatch):
    monkeypatch.setenv("BOOKDROP_INTEGRATION_API_TOKEN", "s3cret")
    get_settings.cache_clear()
    try:
        assert client.get("/api/v1/releases/upcoming").status_code == 401
        assert client.get("/api/v1/stats", headers={"X-API-Key": "wrong"}).status_code == 401

        ok = client.get("/api/v1/releases/upcoming", headers={"Authorization": "Bearer s3cret"})
        assert ok.status_code == 200
        ok = client.get("/api/v1/stats", headers={"X-API-Key": "s3cret"})
        assert ok.status_code == 200
    finally:
        monkeypatch.delenv("BOOKDROP_INTEGRATION_API_TOKEN", raising=False)
        get_settings.cache_clear()


def _ics_events(text: str) -> list[dict[str, str]]:
    unfolded = text.replace("\r\n ", "")
    events: list[dict[str, str]] = []
    for line in unfolded.split("\r\n"):
        if line == "BEGIN:VEVENT":
            events.append({})
        elif events and ":" in line and line != "END:VEVENT":
            name, value = line.split(":", 1)
            events[-1][name] = value
    return events


def test_release_ics_feed(client, seeded):
    resp = client.get("/api/v1/releases.ics")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/calendar")
    assert resp.text.startswith("BEGIN:VCALENDAR\r\n")
    assert resp.text.endswith("END:VCALENDAR\r\n")
    assert all(len(line.encode()) <= 75 for line in resp.text.split("\r\n"))

    events = _ics_events(resp.text)
    summaries = [e["SUMMARY"] for e in events]
    # Editions collapsed, undated skipped, last month's release kept.
    assert summaries == [
        "Old Backlog Title — Robin Hobb",
        "Wind and Truth — Brandon Sanderson",
        "Far Future Audiobook — Robin Hobb",
    ]
    wind = events[1]
    assert wind["DTSTART;VALUE=DATE"] == f"{seeded + timedelta(days=10):%Y%m%d}"
    assert wind["DTEND;VALUE=DATE"] == f"{seeded + timedelta(days=11):%Y%m%d}"
    assert wind["URL"] == "https://www.goodreads.com/search?q=Wind%20and%20Truth%20Brandon%20Sanderson"
    assert len({e["UID"] for e in events}) == 3


def test_release_ics_past_days_and_format(client, seeded):
    resp = client.get("/api/v1/releases.ics", params={"past_days": 0, "format": "audiobook"})
    summaries = [e["SUMMARY"] for e in _ics_events(resp.text)]
    assert summaries == ["Wind and Truth — Brandon Sanderson", "Far Future Audiobook — Robin Hobb"]


def test_release_ics_escapes_and_folds(client, db_session):
    author = Author(name="Le Guin, Ursula K.")
    db_session.add(author)
    db_session.flush()
    long_title = "A Wizard of Earthsea; or, the Long Title " + "é" * 60
    db_session.add(
        Book(
            author_id=author.id,
            title=long_title,
            format=BookFormat.BOOK,
            release_date=date.today() + timedelta(days=3),
            source="google_books",
            series="Earthsea",
            series_sequence="1",
        )
    )
    db_session.commit()

    text = client.get("/api/v1/releases.ics").text
    assert all(len(line.encode()) <= 75 for line in text.split("\r\n"))
    event = _ics_events(text)[0]
    assert event["SUMMARY"] == (
        "A Wizard of Earthsea\\; or\\, the Long Title " + "é" * 60 + " — Le Guin\\, Ursula K."
    )
    assert event["DESCRIPTION"].startswith("Earthsea #1\\nBook by Le Guin\\, Ursula K.\\n")


def test_release_ics_accepts_token_query_param(client, seeded, monkeypatch):
    monkeypatch.setenv("BOOKDROP_INTEGRATION_API_TOKEN", "s3cret")
    get_settings.cache_clear()
    try:
        assert client.get("/api/v1/releases.ics").status_code == 401
        assert client.get("/api/v1/releases.ics", params={"token": "nope"}).status_code == 401
        assert client.get("/api/v1/releases.ics", params={"token": "s3cret"}).status_code == 200
    finally:
        monkeypatch.delenv("BOOKDROP_INTEGRATION_API_TOKEN", raising=False)
        get_settings.cache_clear()
