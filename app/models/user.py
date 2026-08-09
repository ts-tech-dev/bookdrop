from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import NotificationChannel, NotificationFrequency, NotificationMode
from app.utils.time import utcnow

if TYPE_CHECKING:
    from app.models.subscription import AuthorSubscription


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    discord_webhook_url: Mapped[str | None] = mapped_column(String, nullable=True)

    notification_channel: Mapped[NotificationChannel] = mapped_column(
        Enum(NotificationChannel), default=NotificationChannel.EMAIL
    )
    notification_frequency: Mapped[NotificationFrequency] = mapped_column(
        Enum(NotificationFrequency), default=NotificationFrequency.DAILY
    )
    notification_mode: Mapped[NotificationMode] = mapped_column(
        Enum(NotificationMode), default=NotificationMode.NEW_ONLY
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    subscriptions: Mapped[list["AuthorSubscription"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
