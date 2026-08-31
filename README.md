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
| `BOOKDROP_AUDIOBOOKSHELF_IMPORT_INTERVAL_MINUTES` | How often to re-import the author list from Audiobookshelf (default `1440` = daily). `0` disables the scheduled job; the "Import authors" button in the web UI still works. |
| `BOOKDROP_INTEGRATION_API_TOKEN` | If set, `/api/v1` requires it via `Authorization: Bearer <token>` or `X-API-Key`. Unset = open. |
| `BOOKDROP_CORS_ALLOW_ORIGINS` | Comma-separated origins allowed to call the API from a browser, or `*` (default). |

## Integration API

A stable, read-only JSON API under `/api/v1` for other services (e.g. a homepage
dashboard container) to pull upcoming releases. Full schema at
`http://localhost:8000/docs`.

| Endpoint | Description |
| --- | --- |
| `GET /api/v1/releases/upcoming` | Flat list of unreleased titles across all tracked authors, soonest first, undated ("Date TBA") last. Each item carries the author name, cover URL, series info, and `days_until`. Query params: `within_days` (1–1825), `format` (`book`/`audiobook`), `include_undated` (default `true`), `limit` (1–500). |
| `GET /api/v1/releases/calendar` | The same releases grouped into `This month` / individual months / quarters / `Date TBA`, matching the daily digest layout. Accepts `within_days` and `format`. |
| `GET /api/v1/stats` | Counts for an at-a-glance panel: `authors_tracked`, `upcoming_count`, and the single `next_release`. |

Multiple editions of one title (e.g. an Audible and a Google Books row) are collapsed to
a single entry. Responses include a `generated_at` UTC timestamp.

```bash
curl http://localhost:8000/api/v1/releases/upcoming?within_days=90&limit=10
# with a token:
curl -H "X-API-Key: $BOOKDROP_INTEGRATION_API_TOKEN" \
  http://localhost:8000/api/v1/releases/upcoming
```

### Example: [gethomepage.dev](https://gethomepage.dev) custom API widget

```yaml
- Upcoming Books:
    - Bookdrop:
        widget:
          type: customapi
          url: http://bookdrop:8000/api/v1/releases/upcoming?within_days=120&limit=5
          method: GET
          # headers:
          #   X-API-Key: your-token   # only if BOOKDROP_INTEGRATION_API_TOKEN is set
          mappings:
            - field: count
              label: Upcoming
            - field: { releases: { 0: title } }
              label: Next up
            - field: { releases: { 0: days_until } }
              label: Days
              format: number
```
