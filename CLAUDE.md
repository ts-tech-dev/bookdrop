# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Bookdrop tracks authors a user follows and notifies them (Discord or email) when those
authors announce or release new books/audiobooks. Authors are added manually or imported
from a self-hosted Audiobookshelf instance; release data comes from the Audible catalog
(audiobooks) and the Google Books API (print/ebook). It ships as a single Docker container
with a SQLite database — no external services (no Postgres, no Redis/Celery) are required.

## Commands

There is no local Python toolchain assumed — validate through Docker (see "Sandbox note" below
for why this matters in this particular environment).

```bash
# Run the app locally with reload
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload

# Lint / type-check / test
ruff check app tests
mypy app
pytest -q                          # all tests
pytest tests/test_authors.py -q    # single file
pytest tests/test_authors.py::test_create_author_and_subscribe -q  # single test

# Docker (production image + compose stack)
docker compose up --build
```

### Sandbox note

This dev environment has no system `pip`/`venv` and the default Docker bridge network
cannot resolve DNS. If you need to install packages or run `docker build`/`docker run`
here, add `--network host` to the Docker command — `docker build --network host ...` /
`docker run --network host ...`. This is a sandbox quirk, not something the Dockerfile or
docker-compose.yml need to account for.

## Architecture

Layout: `app/main.py` (FastAPI app + lifespan) → `app/api/routes/*` (HTTP layer, one router
per resource) → `app/services/*` (business logic, all external I/O) → `app/models/*`
(SQLAlchemy ORM) / `app/schemas/*` (Pydantic request/response models). `app/config.py` is a
single `pydantic-settings` `Settings` object read from env vars prefixed `BOOKDROP_`
(`.env` in dev, real env vars in the container).

**Release-checking pipeline** (the core of the app, in `app/services/`):
`scheduler.py` runs an APScheduler job on an interval (`BOOKDROP_RELEASE_CHECK_INTERVAL_MINUTES`)
→ `release_tracker.check_for_new_releases()` iterates every tracked `Author`, queries
`audible.py` and `google_books.py` for that author's catalog, and upserts new titles as
`Book` rows (deduped by `(source, external_id)`) → each newly-created `Book` is immediately
handed to `notifier.py`'s `Notifier.notify_for_book()`.

**Notification fan-out logic** lives entirely in `Notifier._due_users_for_book()`
(`app/services/notifier.py`) and is the one place that encodes the product rules:
- A user is notified the first time a book they'd hear about (via an `AuthorSubscription`)
  is seen, regardless of mode.
- After that, a `NotificationMode.NEW_ONLY` user is never notified again for that book.
- A `NotificationMode.UNTIL_RELEASE` user is re-notified once their
  `NotificationFrequency` interval (immediate/daily/weekly, see `_FREQUENCY_INTERVALS`) has
  elapsed since their last `NotificationLog` entry for that book — so the check job can run
  as often as it wants without spamming digest users.
- Delivery itself is a dumb dispatch to `DiscordNotifier` or `EmailNotifier` based on the
  user's `notification_channel`; every send is recorded as a `NotificationLog` row, which is
  both the audit trail and the state `_due_users_for_book` reads back.

**Data model** (`app/models/`): `User` —< `AuthorSubscription` >— `Author` —< `Book` —<
`NotificationLog` >— `User`. `Author.source` and `Book.source` distinguish where a record
came from (`manual`/`audiobookshelf` for authors, `audible`/`google_books` for books) so
importers/pollers can no-op on records they've already created. Enums live in
`app/models/enums.py` as `enum.StrEnum` and are shared verbatim between the ORM layer and
the Pydantic schemas.

**Cross-references between model files use `TYPE_CHECKING`-guarded imports** (not
runtime imports) to avoid circular imports while keeping `relationship()` forward refs
(e.g. `Mapped["Book"]`) resolvable by mypy/ruff. When adding a new relationship, follow
the existing pattern rather than importing the related model at module level.

**Time handling**: DB timestamp columns are timezone-naive UTC. Always use
`app.utils.time.utcnow()` for defaults/comparisons involving those columns — plain
`datetime.utcnow()` is deprecated, and `datetime.now(UTC)` (timezone-aware) will produce
values inconsistent with what's already stored.

**No migrations**: `database.init_db()` calls `Base.metadata.create_all()` on startup;
there's no Alembic. If you add a framework for schema migrations, wire it into both
`init_db()` and the Docker startup path.

**Tests** (`tests/conftest.py`): the `client` fixture overrides `get_db` with a SQLite
in-memory engine using `StaticPool` — required because `:memory:` SQLite is
per-connection, and `TestClient` executes requests in a worker thread. It also
deliberately does *not* enter `TestClient` as a context manager, so FastAPI's `lifespan`
(and therefore `init_db()`/the APScheduler startup) never runs; every test hits the
in-memory DB through the `get_db` override regardless.
