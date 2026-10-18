from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Recommendation
from app.schemas.recommendation import RecommendationRead
from app.services.recommendations import (
    AudibleUnavailableError,
    list_recommendations,
    refresh_recommendations,
)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("", response_model=list[RecommendationRead])
def get_recommendations(db: Session = Depends(get_db)) -> list[Recommendation]:
    return list_recommendations(db)


@router.post("/refresh", response_model=list[RecommendationRead])
async def refresh(db: Session = Depends(get_db)) -> list[Recommendation]:
    try:
        return await refresh_recommendations(db)
    except AudibleUnavailableError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
