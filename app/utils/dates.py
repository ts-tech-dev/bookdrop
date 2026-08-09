from datetime import date, datetime


def parse_date(value: str | None) -> date | None:
    """Best-effort parse of the loose date formats returned by Audible/Google Books."""
    if not value:
        return None

    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    return None
