from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Author, AuthorSubscription, User
from app.models.enums import AuthorSource
from app.schemas.author import AuthorCreate, AuthorRead
from app.services.subscriptions import subscribe_all_users_to_author

router = APIRouter(prefix="/authors", tags=["authors"])


@router.get("", response_model=list[AuthorRead])
def list_authors(db: Session = Depends(get_db)) -> list[Author]:
    return db.query(Author).all()


@router.post("", response_model=AuthorRead, status_code=201)
def create_author(payload: AuthorCreate, db: Session = Depends(get_db)) -> Author:
    author = Author(name=payload.name, source=AuthorSource.MANUAL)
    db.add(author)
    db.commit()
    db.refresh(author)
    subscribe_all_users_to_author(db, author)
    return author


@router.delete("/{author_id}", status_code=204)
def delete_author(author_id: int, db: Session = Depends(get_db)) -> None:
    author = db.get(Author, author_id)
    if author is None:
        raise HTTPException(status_code=404, detail="Author not found")
    db.delete(author)
    db.commit()


@router.post("/{author_id}/subscribe/{user_id}", status_code=201)
def subscribe(author_id: int, user_id: int, db: Session = Depends(get_db)) -> dict:
    author = db.get(Author, author_id)
    user = db.get(User, user_id)
    if author is None or user is None:
        raise HTTPException(status_code=404, detail="Author or user not found")

    exists = (
        db.query(AuthorSubscription)
        .filter(AuthorSubscription.author_id == author_id, AuthorSubscription.user_id == user_id)
        .first()
    )
    if exists is None:
        db.add(AuthorSubscription(author_id=author_id, user_id=user_id))
        db.commit()

    return {"status": "subscribed"}


@router.delete("/{author_id}/subscribe/{user_id}", status_code=204)
def unsubscribe(author_id: int, user_id: int, db: Session = Depends(get_db)) -> None:
    subscription = (
        db.query(AuthorSubscription)
        .filter(AuthorSubscription.author_id == author_id, AuthorSubscription.user_id == user_id)
        .first()
    )
    if subscription is None:
        raise HTTPException(status_code=404, detail="Subscription not found")

    db.delete(subscription)
    db.commit()
