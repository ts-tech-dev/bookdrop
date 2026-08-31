from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, model_validator

from app.models.enums import BookFormat, BookStatus
from app.utils.dates import derive_book_status


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

    @model_validator(mode="after")
    def _resolve_status(self) -> "BookRead":
        # The stored status column is never updated after ingest; derive the real value
        # from the release date so a shipped book doesn't keep showing as "announced".
        self.status = derive_book_status(self.release_date)
        return self
