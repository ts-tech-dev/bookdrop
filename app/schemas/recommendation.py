from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import RecommendationKind


class RecommendationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: RecommendationKind
    asin: str
    title: str
    author_name: str | None
    cover_url: str | None
    release_date: date | None
    series: str | None
    series_sequence: str | None
    url: str | None
    reason: str
    score: float
    created_at: datetime
