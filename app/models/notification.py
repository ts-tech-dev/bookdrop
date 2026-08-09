from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import NotificationChannel
from app.utils.time import utcnow

if TYPE_CHECKING:
    from app.models.book import Book
    from app.models.user import User


class NotificationLog(Base):
    __tablename__ = "notification_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"))
    channel: Mapped[NotificationChannel] = mapped_column(Enum(NotificationChannel))
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    user: Mapped["User"] = relationship()
    book: Mapped["Book"] = relationship(back_populates="notifications")
