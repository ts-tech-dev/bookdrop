import logging
from datetime import UTC, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import get_settings
from app.database import SessionLocal
from app.services.audiobookshelf import import_authors
from app.services.digest import send_daily_digests
from app.services.release_tracker import check_for_new_releases

logger = logging.getLogger(__name__)

_scheduler = AsyncIOScheduler()

# A fixed anchor (not "now") for the interval trigger, so the check grid stays aligned
# across restarts instead of resetting to "interval minutes from whenever we last booted".
_INTERVAL_ANCHOR = datetime(2000, 1, 1, tzinfo=UTC)


def start_scheduler() -> None:
    settings = get_settings()

    _scheduler.add_job(
        _run_release_check,
        "interval",
        minutes=settings.release_check_interval_minutes,
        start_date=_INTERVAL_ANCHOR,
        id="release_check",
        replace_existing=True,
    )
    _scheduler.add_job(
        _run_daily_digest,
        "cron",
        hour=settings.daily_digest_hour_utc,
        id="daily_digest",
        replace_existing=True,
    )
    if settings.audiobookshelf_import_interval_minutes > 0:
        _scheduler.add_job(
            _run_author_import,
            "interval",
            minutes=settings.audiobookshelf_import_interval_minutes,
            start_date=_INTERVAL_ANCHOR,
            id="author_import",
            replace_existing=True,
        )
    _scheduler.start()


def stop_scheduler() -> None:
    _scheduler.shutdown(wait=False)


async def _run_release_check() -> None:
    db = SessionLocal()
    try:
        await check_for_new_releases(db)
    finally:
        db.close()


async def _run_daily_digest() -> None:
    db = SessionLocal()
    try:
        await send_daily_digests(db)
    finally:
        db.close()


async def _run_author_import() -> None:
    db = SessionLocal()
    try:
        imported = await import_authors(db)
        if imported:
            logger.info("Imported %d new author(s) from Audiobookshelf", len(imported))
    except RuntimeError:
        # Audiobookshelf not configured — nothing to do on this schedule.
        logger.debug("Skipping Audiobookshelf author import: not configured")
    except Exception:
        logger.exception("Audiobookshelf author import failed")
    finally:
        db.close()
