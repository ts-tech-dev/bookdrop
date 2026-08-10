from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import BookFormat, BookStatus


class BookRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    author_id: int
    title: str
    format: BookFormat
    status: BookStatus
    announced_date: date | None
    release_date: date | None
    source: str
    cover_url: str | None
    series: str | None
    series_sequence: str | None
    created_at: datetime
