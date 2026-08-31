from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Author
from app.schemas.author import AuthorRead
from app.services.audiobookshelf import import_authors as import_authors_from_abs

router = APIRouter(prefix="/audiobookshelf", tags=["audiobookshelf"])


@router.post("/import-authors", response_model=list[AuthorRead])
async def import_authors(db: Session = Depends(get_db)) -> list[Author]:
    try:
        return await import_authors_from_abs(db)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
