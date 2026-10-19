from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import AuthorSource
from app.utils.time import utcnow

if TYPE_CHECKING:
    from app.models.book import Book
    from app.models.dismissal import DismissedBook
    from app.models.subscription import AuthorSubscription


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, index=True)
    source: Mapped[AuthorSource] = mapped_column(Enum(AuthorSource), default=AuthorSource.MANUAL)

    audible_author_id: Mapped[str | None] = mapped_column(String, nullable=True, unique=True)
    google_books_author_id: Mapped[str | None] = mapped_column(String, nullable=True)
    audiobookshelf_author_id: Mapped[str | None] = mapped_column(String, nullable=True, unique=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    books: Mapped[list["Book"]] = relationship(
        back_populates="author", cascade="all, delete-orphan"
    )
    subscribers: Mapped[list["AuthorSubscription"]] = relationship(
        back_populates="author", cascade="all, delete-orphan"
    )
    dismissed_books: Mapped[list["DismissedBook"]] = relationship(
        back_populates="author", cascade="all, delete-orphan"
    )
