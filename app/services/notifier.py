import logging
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import AuthorSubscription, Book, NotificationLog, User
from app.models.enums import NotificationChannel, NotificationFrequency, NotificationMode
from app.services.discord import DiscordNotifier, book_embed
from app.services.dismissals import is_dismissed
from app.services.email import EmailNotifier
from app.utils.time import utcnow

logger = logging.getLogger(__name__)

_FREQUENCY_INTERVALS = {
    NotificationFrequency.IMMEDIATE: timedelta(0),
    NotificationFrequency.DAILY: timedelta(days=1),
    NotificationFrequency.WEEKLY: timedelta(days=7),
}

# How long after release a book still counts as a "new release" worth notifying about.
_RECENTLY_RELEASED_WINDOW = timedelta(days=120)


def _is_notification_worthy(book: Book) -> bool:
    """True for books that are still upcoming/announced, or were released recently.

    Excludes older backlog titles (e.g. an author's decades-old back catalog picked up
    the first time we start tracking them), which aren't a "new release" a user asked
    to hear about.
    """
    if book.release_date is None:
        return True
    return date.today() - book.release_date <= _RECENTLY_RELEASED_WINDOW


class Notifier:
    """Decides who is due a notification for a book and sends it on their chosen channel.

    A user is notified once when a book is first seen. After that, only users in
    `until_release` mode are re-notified, and only once their notification_frequency
    interval has elapsed since their last notification for that book.
    """

    def __init__(self, db: Session) -> None:
        self._db = db
        self._discord = DiscordNotifier()
        self._email = EmailNotifier()

    def _due_users_for_book(self, book: Book) -> list[User]:
        subscriptions = (
            self._db.query(AuthorSubscription)
            .filter(AuthorSubscription.author_id == book.author_id)
            .all()
        )

        due = []
        for subscription in subscriptions:
            user = subscription.user
            last_sent = (
                self._db.query(NotificationLog)
                .filter(NotificationLog.user_id == user.id, NotificationLog.book_id == book.id)
                .order_by(NotificationLog.sent_at.desc())
                .first()
            )

            if last_sent is None:
                due.append(user)
                continue

            if user.notification_mode == NotificationMode.NEW_ONLY:
                continue

            interval = _FREQUENCY_INTERVALS[user.notification_frequency]
            if utcnow() - last_sent.sent_at >= interval:
                due.append(user)

        return due

    async def notify_for_book(self, book: Book) -> None:
        if not _is_notification_worthy(book):
            logger.info(
                "Skipping notification for book %d (%r): release date %s is not recent",
                book.id,
                book.title,
                book.release_date,
            )
            return

        if is_dismissed(self._db, book):
            logger.info("Skipping notification for book %d (%r): dismissed", book.id, book.title)
            return

        series_part = ""
        if book.series:
            series_part = f" [{book.series} #{book.series_sequence}]" if book.series_sequence else f" [{book.series}]"

        for user in self._due_users_for_book(book):
            message = (
                f"{book.author.name} - {book.title}{series_part} ({book.format.value}) "
                f"releases {book.release_date}"
            )

            wants_discord = user.notification_channel == NotificationChannel.DISCORD
            webhook_url = user.discord_webhook_url or get_settings().discord_webhook_url
            try:
                if wants_discord and webhook_url:
                    await self._discord.send(webhook_url, embeds=[book_embed(book)])
                elif user.notification_channel == NotificationChannel.EMAIL and user.email:
                    self._email.send(user.email, f"New release: {book.title}", message)
                else:
                    logger.warning(
                        "Skipping notification for user %d: channel %s has no destination configured",
                        user.id,
                        user.notification_channel.value,
                    )
                    continue
            except Exception:
                logger.exception("Failed to send notification to user %d for book %d", user.id, book.id)
                continue

            logger.info("Notified user %d via %s for book %d", user.id, user.notification_channel.value, book.id)
            self._db.add(
                NotificationLog(user_id=user.id, book_id=book.id, channel=user.notification_channel)
            )

        self._db.commit()
