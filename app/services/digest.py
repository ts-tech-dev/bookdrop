import logging
from datetime import date

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import AuthorSubscription, Book, User
from app.models.enums import NotificationChannel
from app.services.discord import DiscordNotifier, book_embed, bucket_embeds, section_header_embed
from app.services.email import EmailNotifier

logger = logging.getLogger(__name__)

# Discord caps a single message at 10 embeds and 6000 total embed characters;
# leave headroom on the character budget.
_DISCORD_EMBEDS_PER_MESSAGE = 10
_DISCORD_EMBED_CHARS_LIMIT = 5500


def _embed_length(embed: dict) -> int:
    length = len(embed.get("title", "")) + len(embed.get("description", ""))
    for field in embed.get("fields", []):
        length += len(field.get("name", "")) + len(field.get("value", ""))
    return length


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


def _add_months(d: date, months: int) -> date:
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, 1)


def _quarter_label(d: date) -> str:
    quarter = (d.month - 1) // 3 + 1
    return f"Q{quarter} {d.year}"


def _bucket_info(release_date: date | None, today: date) -> tuple[str, bool]:
    """Returns (label, full_detail) - full_detail marks the near-term buckets that are worth

    showing with cover art and per-book detail rather than a compact grouped list.
    """
    if release_date is None:
        return "Date TBA", False

    this_month_start = date(today.year, today.month, 1)
    next_month_start = _add_months(this_month_start, 1)
    month3_start = _add_months(this_month_start, 2)
    beyond_start = _add_months(this_month_start, 3)

    if release_date < next_month_start:
        return "This month", True
    if release_date < month3_start:
        return next_month_start.strftime("%B %Y"), True
    if release_date < beyond_start:
        return month3_start.strftime("%B %Y"), False
    return _quarter_label(release_date), False


def bucket_books(
    books: list[Book], today: date | None = None
) -> tuple[dict[str, list[Book]], set[str]]:
    """Groups books into This month / the next two individual months / quarters beyond that.

    Buckets are chronological and non-overlapping, so a book lands in exactly one of them.
    "Date TBA" (announced, no release date yet) is always last, regardless of where such a
    book happened to sort in `books`. Also returns the set of "full detail" bucket labels
    (This month and next month) - the near-term buckets worth rendering with full per-book
    detail (e.g. cover art) rather than a compact grouped list.
    """
    today = today or date.today()
    buckets: dict[str, list[Book]] = {}
    full_detail_labels: set[str] = set()
    tba: list[Book] = []

    for book in books:
        label, full_detail = _bucket_info(book.release_date, today)
        if label == "Date TBA":
            tba.append(book)
            continue
        buckets.setdefault(label, []).append(book)
        if full_detail:
            full_detail_labels.add(label)

    if tba:
        buckets["Date TBA"] = tba

    return buckets, full_detail_labels


def _format_line(book: Book) -> str:
    series = ""
    if book.series:
        series = f" ({book.series} #{book.series_sequence})" if book.series_sequence else f" ({book.series})"
    release = book.release_date.isoformat() if book.release_date else "date TBA"
    return f"- {book.author.name} - {book.title}{series} - {release}"


async def _send_discord_digest(
    webhook_url: str, buckets: dict[str, list[Book]], full_detail_labels: set[str]
) -> None:
    discord = DiscordNotifier()
    all_embeds: list[dict] = []
    for label, books in buckets.items():
        if label in full_detail_labels:
            all_embeds.append(section_header_embed(label))
            all_embeds.extend(book_embed(book) for book in books)
        else:
            all_embeds.extend(bucket_embeds(label, books))

    embeds: list[dict] = []
    chars = 0
    first_message = True

    async def flush() -> None:
        nonlocal embeds, chars, first_message
        if not embeds:
            return
        content = "**Upcoming books**" if first_message else ""
        await discord.send(webhook_url, content, embeds=embeds)
        embeds = []
        chars = 0
        first_message = False

    for embed in all_embeds:
        length = _embed_length(embed)
        over_count = len(embeds) >= _DISCORD_EMBEDS_PER_MESSAGE
        over_chars = chars + length > _DISCORD_EMBED_CHARS_LIMIT
        if embeds and (over_count or over_chars):
            await flush()
        embeds.append(embed)
        chars += length

    await flush()


def _send_email_digest(to_address: str, buckets: dict[str, list[Book]]) -> None:
    sections = []
    for label, books in buckets.items():
        lines = "\n".join(_format_line(book) for book in books)
        sections.append(f"{label}\n{'-' * len(label)}\n{lines}")
    body = "Upcoming books\n\n" + "\n\n".join(sections)
    EmailNotifier().send(to_address, "Bookdrop: upcoming books", body)


async def send_digest_to_user(db: Session, user: User) -> int:
    """Sends the user's digest and returns how many books it contained (0 if skipped)."""
    books = upcoming_books_for_user(db, user)
    if not books:
        return 0
    buckets, full_detail_labels = bucket_books(books)

    if user.notification_channel == NotificationChannel.DISCORD:
        webhook_url = user.discord_webhook_url or get_settings().discord_webhook_url
        if not webhook_url:
            logger.warning("Skipping digest for user %d: no Discord webhook configured", user.id)
            return 0
        await _send_discord_digest(webhook_url, buckets, full_detail_labels)
    elif user.notification_channel == NotificationChannel.EMAIL:
        if not user.email:
            logger.warning("Skipping digest for user %d: no email address", user.id)
            return 0
        _send_email_digest(user.email, buckets)

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
