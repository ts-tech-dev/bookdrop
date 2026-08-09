from datetime import timedelta

from sqlalchemy.orm import Session

from app.models import AuthorSubscription, Book, NotificationLog, User
from app.models.enums import NotificationChannel, NotificationFrequency, NotificationMode
from app.services.discord import DiscordNotifier
from app.services.email import EmailNotifier
from app.utils.time import utcnow

_FREQUENCY_INTERVALS = {
    NotificationFrequency.IMMEDIATE: timedelta(0),
    NotificationFrequency.DAILY: timedelta(days=1),
    NotificationFrequency.WEEKLY: timedelta(days=7),
}


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
        for user in self._due_users_for_book(book):
            message = (
                f"{book.author.name} - {book.title} ({book.format.value}) "
                f"releases {book.release_date}"
            )

            wants_discord = user.notification_channel == NotificationChannel.DISCORD
            if wants_discord and user.discord_webhook_url:
                await self._discord.send(user.discord_webhook_url, message)
            elif user.notification_channel == NotificationChannel.EMAIL and user.email:
                self._email.send(user.email, f"New release: {book.title}", message)
            else:
                continue

            self._db.add(
                NotificationLog(user_id=user.id, book_id=book.id, channel=user.notification_channel)
            )

        self._db.commit()
