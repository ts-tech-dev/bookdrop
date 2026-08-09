from datetime import UTC, datetime


def utcnow() -> datetime:
    """Naive UTC timestamp, matching the storage format of the (timezone-naive) DateTime columns."""
    return datetime.now(UTC).replace(tzinfo=None)
