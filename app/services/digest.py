import logging
from datetime import date

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import AuthorSubscription, Book, User
from app.models.enums import NotificationChannel
from app.services.discord import DiscordNotifier
from app.services.email import EmailNotifier

logger = logging.getLogger(__name__)

# Discord webhook messages are capped at 2000 characters; leave headroom.
_DISCORD_CHUNK_LIMIT = 1900


def upcoming_books_for_user(db: Session, user: User) -> list[Book]:
    author_ids = [
        row.author_id
        for row in db.query(AuthorSubscription).filter(AuthorSubscription.user_id == user.id)
    ]
    if not author_ids:
        return []

    books = (
        db.query(Book)
        .filter(
            Book.author_id.in_(author_ids),
            (Book.release_date.is_(None)) | (Book.release_date >= date.today()),
        )
        .order_by(Book.release_date.asc())
        .all()
    )

    # Collapse multiple editions of the same title, same as the web UI and notifications.
    deduped: dict[tuple[int, str], Book] = {}
    for book in books:
        key = (book.author_id, book.title.strip().lower())
        deduped.setdefault(key, book)
    return list(deduped.values())


def _format_line(book: Book) -> str:
    series = ""
    if book.series:
        series = f" ({book.series} #{book.series_sequence})" if book.series_sequence else f" ({book.series})"
    release = book.release_date.isoformat() if book.release_date else "date TBA"
    return f"- {book.author.name} - {book.title}{series} - {release}"


async def _send_discord_digest(webhook_url: str, books: list[Book]) -> None:
    discord = DiscordNotifier()
    chunk = "**Upcoming books**"
    for book in books:
        line = _format_line(book)
        if len(chunk) + 1 + len(line) > _DISCORD_CHUNK_LIMIT:
            await discord.send(webhook_url, chunk)
            chunk = line
        else:
            chunk = f"{chunk}\n{line}"
    if chunk:
        await discord.send(webhook_url, chunk)


def _send_email_digest(to_address: str, books: list[Book]) -> None:
    body = "Upcoming books\n\n" + "\n".join(_format_line(book) for book in books)
    EmailNotifier().send(to_address, "Bookdrop: upcoming books", body)


async def send_digest_to_user(db: Session, user: User) -> int:
    """Sends the user's digest and returns how many books it contained (0 if skipped)."""
    books = upcoming_books_for_user(db, user)
    if not books:
        return 0

    if user.notification_channel == NotificationChannel.DISCORD:
        webhook_url = user.discord_webhook_url or get_settings().discord_webhook_url
        if not webhook_url:
            logger.warning("Skipping digest for user %d: no Discord webhook configured", user.id)
            return 0
        await _send_discord_digest(webhook_url, books)
    elif user.notification_channel == NotificationChannel.EMAIL:
        if not user.email:
            logger.warning("Skipping digest for user %d: no email address", user.id)
            return 0
        _send_email_digest(user.email, books)

    return len(books)


async def send_daily_digests(db: Session) -> None:
    users = db.query(User).all()
    logger.info("Sending daily digests to %d users", len(users))

    for user in users:
        try:
            book_count = await send_digest_to_user(db, user)
        except Exception:
            logger.exception("Failed to send daily digest to user %d", user.id)
            continue

        if book_count:
            logger.info("Sent daily digest to user %d (%d books)", user.id, book_count)

    logger.info("Daily digest run complete")
