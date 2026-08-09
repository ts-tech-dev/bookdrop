from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import get_settings
from app.database import SessionLocal
from app.services.release_tracker import check_for_new_releases

_scheduler = AsyncIOScheduler()


def start_scheduler() -> None:
    settings = get_settings()

    _scheduler.add_job(
        _run_release_check,
        "interval",
        minutes=settings.release_check_interval_minutes,
        id="release_check",
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
