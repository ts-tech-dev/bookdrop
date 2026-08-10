from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import BookFormat, BookStatus
from app.utils.time import utcnow

if TYPE_CHECKING:
    from app.models.author import Author
    from app.models.notification import NotificationLog


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"))

    title: Mapped[str] = mapped_column(String, index=True)
    format: Mapped[BookFormat] = mapped_column(Enum(BookFormat))
    status: Mapped[BookStatus] = mapped_column(Enum(BookStatus), default=BookStatus.ANNOUNCED)

    announced_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    release_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    source: Mapped[str] = mapped_column(String)  # "audible" | "google_books"
    external_id: Mapped[str | None] = mapped_column(String, nullable=True)
    cover_url: Mapped[str | None] = mapped_column(String, nullable=True)

    series: Mapped[str | None] = mapped_column(String, nullable=True)
    series_sequence: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    author: Mapped["Author"] = relationship(back_populates="books")
    notifications: Mapped[list["NotificationLog"]] = relationship(
        back_populates="book", cascade="all, delete-orphan"
    )
