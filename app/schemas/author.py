from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import AuthorSource


class AuthorCreate(BaseModel):
    name: str


class AuthorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    source: AuthorSource
    created_at: datetime
