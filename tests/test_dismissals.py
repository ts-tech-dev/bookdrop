import asyncio
from datetime import date, timedelta

import pytest

from app.models import Author, AuthorSubscription, Book, DismissedBook, NotificationLog, User
from app.models.enums import BookFormat, BookStatus, NotificationChannel
from app.services import notifier as notifier_module
from app.services.digest import upcoming_books_for_user
from app.services.notifier import Notifier


@pytest.fixture()
def shelf(db_session):
    """One author with two editions of an upcoming title plus another upcoming title."""
    soon = date.today() + timedelta(days=30)
    author = Author(name="Robin Hobb")
    db_session.add(author)
    db_session.flush()

    def book(title, source, external_id, fmt=BookFormat.AUDIOBOOK):
        return Book(
            author_id=author.id,
            title=title,
            format=fmt,
            status=BookStatus.ANNOUNCED,
            release_date=soon,
            source=source,
            external_id=external_id,
        )

    audible = book("Skip This One", "audible", "A1")
    google = book("skip this one ", "google_books", "G1", BookFormat.BOOK)  # same title
    keep = book("Keep This One", "audible", "A2")
    db_session.add_all([audible, google, keep])
    db_session.commit()
    return {"author": author, "audible": audible, "google": google, "keep": keep}


def _titles(client, **params):
    return sorted(b["title"] for b in client.get("/books", params=params).json())


def test_dismiss_hides_every_edition_and_restore_brings_it_back(client, shelf):
    assert _titles(client) == ["Keep This One", "Skip This One"]

    assert client.post(f"/books/{shelf['audible'].id}/dismiss").status_code == 204
    assert _titles(client) == ["Keep This One"]

    # The other edition is covered by the same dismissal.
    flagged = {
        b["title"]: b["dismissed"]
        for b in client.get("/books", params={"include_dismissed": True}).json()
    }
    assert flagged == {"Keep This One": False, "Skip This One": True}

    # Restoring through either edition works.
    assert client.delete(f"/books/{shelf['google'].id}/dismiss").status_code == 204
    assert _titles(client) == ["Keep This One", "Skip This One"]


def test_dismiss_is_idempotent_and_404s_for_unknown_books(client, db_session, shelf):
    client.post(f"/books/{shelf['audible'].id}/dismiss")
    client.post(f"/books/{shelf['google'].id}/dismiss")

    assert db_session.query(DismissedBook).count() == 1
    assert client.post("/books/9999/dismiss").status_code == 404
    assert client.delete("/books/9999/dismiss").status_code == 404


def test_dismissed_books_leave_digest_and_integration_api(client, db_session, shelf):
    user = User(email="reader@example.com", notification_channel=NotificationChannel.EMAIL)
    db_session.add(user)
    db_session.flush()
    db_session.add(AuthorSubscription(user_id=user.id, author_id=shelf["author"].id))
    db_session.commit()

    client.post(f"/books/{shelf['audible'].id}/dismiss")

    assert [b.title for b in upcoming_books_for_user(db_session, user)] == ["Keep This One"]
    releases = client.get("/api/v1/releases/upcoming").json()["releases"]
    assert [r["title"] for r in releases] == ["Keep This One"]


def test_dismissed_books_are_not_notified(db_session, shelf, monkeypatch):
    user = User(email="reader@example.com", notification_channel=NotificationChannel.EMAIL)
    db_session.add(user)
    db_session.flush()
    db_session.add(AuthorSubscription(user_id=user.id, author_id=shelf["author"].id))
    db_session.commit()

    sent: list[str] = []
    monkeypatch.setattr(
        notifier_module.EmailNotifier, "send", lambda self, to, subject, body: sent.append(subject)
    )
    dismissal = DismissedBook(
        author_id=shelf["author"].id, title_key="skip this one", title="Skip This One"
    )
    db_session.add(dismissal)
    db_session.commit()

    notifier = Notifier(db_session)
    asyncio.run(notifier.notify_for_book(shelf["google"]))
    asyncio.run(notifier.notify_for_book(shelf["keep"]))

    assert sent == ["New release: Keep This One"]
    assert db_session.query(NotificationLog).count() == 1


def test_deleting_an_author_removes_their_dismissals(client, db_session, shelf):
    client.post(f"/books/{shelf['audible'].id}/dismiss")

    assert client.delete(f"/authors/{shelf['author'].id}").status_code == 204
    assert db_session.query(DismissedBook).count() == 0
