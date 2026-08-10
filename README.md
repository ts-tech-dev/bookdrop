# Bookdrop

Bookdrop tracks authors you care about and notifies you (via Discord or email) when they
announce or release new books and audiobooks.

## Features

- Manually add authors to follow, or import your author list from an
  [Audiobookshelf](https://www.audiobookshelf.org/) instance.
- Looks up new and upcoming titles via the Audible catalog and the Google Books API.
- Sends each user a daily digest of every upcoming book across their subscribed authors,
  in addition to per-release notifications.
- Per-user notification settings:
  - **Channel**: Discord webhook or email.
  - **Frequency**: immediate, daily digest, or weekly digest.
  - **Mode**: notify once when a book is announced (`new_only`), or keep notifying on every
    check until the book is released (`until_release`).
- Ships as a single Docker container with a SQLite database.

## Running with Docker

```bash
cp .env.example .env   # fill in the values you need
docker compose up --build
```

The API is available at `http://localhost:8000`, with interactive docs at
`http://localhost:8000/docs`.

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

uvicorn app.main:app --reload
```

## Configuration

All configuration is via environment variables (see `.env.example`), prefixed with
`BOOKDROP_`. Notable ones:

| Variable | Purpose |
| --- | --- |
| `BOOKDROP_DATABASE_URL` | SQLAlchemy database URL (defaults to a local SQLite file). |
| `BOOKDROP_DISCORD_WEBHOOK_URL` | Default Discord webhook, if not set per-user. |
| `BOOKDROP_SMTP_*` | SMTP server used to send email notifications. |
| `BOOKDROP_AUDIOBOOKSHELF_URL` / `BOOKDROP_AUDIOBOOKSHELF_API_TOKEN` | Audiobookshelf instance to import authors from. |
| `BOOKDROP_GOOGLE_BOOKS_API_KEY` | Optional API key for higher Google Books rate limits. |
| `BOOKDROP_AUDIBLE_MARKETPLACE` | Audible marketplace to query (`us`, `uk`, `de`, `fr`, `ca`, `au`). |
| `BOOKDROP_RELEASE_CHECK_INTERVAL_MINUTES` | How often to poll Audible/Google Books for tracked authors. |
| `BOOKDROP_DAILY_DIGEST_HOUR_UTC` | Hour of day (UTC, 0-23) each user gets a digest of all upcoming books for their subscribed authors. |
