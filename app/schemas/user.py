from pydantic import BaseModel, ConfigDict

from app.models.enums import NotificationChannel, NotificationFrequency, NotificationMode


class UserBase(BaseModel):
    email: str | None = None
    discord_webhook_url: str | None = None
    notification_channel: NotificationChannel = NotificationChannel.EMAIL
    notification_frequency: NotificationFrequency = NotificationFrequency.DAILY
    notification_mode: NotificationMode = NotificationMode.NEW_ONLY


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    email: str | None = None
    discord_webhook_url: str | None = None
    notification_channel: NotificationChannel | None = None
    notification_frequency: NotificationFrequency | None = None
    notification_mode: NotificationMode | None = None


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
