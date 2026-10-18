from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import RecommendationKind
from app.utils.time import utcnow


class Recommendation(Base):
    """A title suggested from the Audiobookshelf library, shared by every user.

    The whole table is replaced on each refresh (see ``services.recommendations``), so rows
    are a cached snapshot rather than state that accumulates.
    """

    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[RecommendationKind] = mapped_column(Enum(RecommendationKind))

    asin: Mapped[str] = mapped_column(String, unique=True)
    title: Mapped[str] = mapped_column(String)
    author_name: Mapped[str | None] = mapped_column(String, nullable=True)
    cover_url: Mapped[str | None] = mapped_column(String, nullable=True)
    release_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    series: Mapped[str | None] = mapped_column(String, nullable=True)
    series_sequence: Mapped[str | None] = mapped_column(String, nullable=True)
    url: Mapped[str | None] = mapped_column(String, nullable=True)

    reason: Mapped[str] = mapped_column(String)
    score: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
