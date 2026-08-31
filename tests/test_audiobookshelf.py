import asyncio

import pytest

from app.models import Author, AuthorSubscription
from app.services import audiobookshelf
from app.services.audiobookshelf import import_authors


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture()
def fake_remote_authors(monkeypatch):
    """Stub the Audiobookshelf HTTP call with a controllable author list."""
    authors: list[dict] = []

    async def _list_authors(self):
        return list(authors)

    monkeypatch.setattr(audiobookshelf.AudiobookshelfClient, "list_authors", _list_authors)
    return authors


def test_import_authors_creates_new_rows_and_subscribes_users(
    client, db_session, fake_remote_authors
):
    client.post("/users", json={"email": "reader@example.com"})
    fake_remote_authors.extend(
        [{"id": "abs-1", "name": "Robin Hobb"}, {"id": "abs-2", "name": "N. K. Jemisin"}]
    )

    imported = _run(import_authors(db_session))

    assert {a.name for a in imported} == {"Robin Hobb", "N. K. Jemisin"}
    assert db_session.query(Author).count() == 2
    # Existing users get an AuthorSubscription for each imported author.
    assert db_session.query(AuthorSubscription).count() == 2


def test_import_authors_is_idempotent(client, db_session, fake_remote_authors):
    fake_remote_authors.append({"id": "abs-1", "name": "Robin Hobb"})

    first = _run(import_authors(db_session))
    second = _run(import_authors(db_session))

    assert len(first) == 1
    assert second == []
    assert db_session.query(Author).count() == 1


def test_import_authors_endpoint_uses_shared_logic(client, fake_remote_authors):
    fake_remote_authors.append({"id": "abs-9", "name": "Tamsyn Muir"})

    res = client.post("/audiobookshelf/import-authors")

    assert res.status_code == 200
    assert [a["name"] for a in res.json()] == ["Tamsyn Muir"]


def test_import_authors_endpoint_400_when_not_configured(client, monkeypatch):
    async def _raise(self):
        raise RuntimeError("Audiobookshelf is not configured")

    monkeypatch.setattr(audiobookshelf.AudiobookshelfClient, "list_authors", _raise)

    res = client.post("/audiobookshelf/import-authors")

    assert res.status_code == 400
    assert res.json()["detail"] == "Audiobookshelf is not configured"
