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
