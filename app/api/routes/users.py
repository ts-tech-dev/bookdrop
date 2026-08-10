from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import User
from app.models.enums import NotificationChannel
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.discord import DiscordNotifier
from app.services.email import EmailNotifier
from app.services.subscriptions import subscribe_user_to_all_authors

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db)) -> list[User]:
    return db.query(User).all()


@router.post("", response_model=UserRead, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    user = User(**payload.model_dump())
    db.add(user)
    db.commit()
    db.refresh(user)
    subscribe_user_to_all_authors(db, user)
    return user


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserRead)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db)) -> None:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()


@router.post("/{user_id}/test-notification")
async def send_test_notification(user_id: int, db: Session = Depends(get_db)) -> dict:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    message = "Bookdrop test notification - if you see this, notifications are working."

    try:
        if user.notification_channel == NotificationChannel.DISCORD:
            webhook_url = user.discord_webhook_url or get_settings().discord_webhook_url
            if not webhook_url:
                raise HTTPException(status_code=400, detail="No Discord webhook configured")
            await DiscordNotifier().send(webhook_url, message)
        elif user.notification_channel == NotificationChannel.EMAIL:
            if not user.email:
                raise HTTPException(status_code=400, detail="User has no email address")
            EmailNotifier().send(user.email, "Bookdrop test notification", message)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to send test notification: {exc}") from exc

    return {"status": "sent", "channel": user.notification_channel.value}
