from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.time import utcnow

if TYPE_CHECKING:
    from app.models.author import Author


class DismissedBook(Base):
    """A title the user isn't interested in: hidden from the shelf, the digest and the
    integration API, and never notified about.

    Keyed on (author, normalized title) rather than a ``Book`` row, so it covers every
    edition of the title (Audible and Google Books, current and future) and survives the
    release checker re-ingesting it.
    """

    __tablename__ = "dismissed_books"
    __table_args__ = (UniqueConstraint("author_id", "title_key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"))
    title_key: Mapped[str] = mapped_column(String)
    title: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    author: Mapped["Author"] = relationship(back_populates="dismissed_books")
