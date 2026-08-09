import enum


class BookFormat(enum.StrEnum):
    BOOK = "book"
    AUDIOBOOK = "audiobook"


class BookStatus(enum.StrEnum):
    ANNOUNCED = "announced"
    RELEASED = "released"


class AuthorSource(enum.StrEnum):
    MANUAL = "manual"
    AUDIOBOOKSHELF = "audiobookshelf"


class NotificationChannel(enum.StrEnum):
    DISCORD = "discord"
    EMAIL = "email"


class NotificationFrequency(enum.StrEnum):
    IMMEDIATE = "immediate"
    DAILY = "daily"
    WEEKLY = "weekly"


class NotificationMode(enum.StrEnum):
    NEW_ONLY = "new_only"
    UNTIL_RELEASE = "until_release"
