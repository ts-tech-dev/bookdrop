from typing import Any

import httpx

from app.models import Book

# Discord's "blurple".
_EMBED_COLOR = 0x5865F2

# Discord's hard per-embed limits.
_MAX_FIELDS_PER_EMBED = 25
_MAX_EMBED_CHARS = 5500


def book_embed(book: Book) -> dict[str, Any]:
    fields = [
        {"name": "Format", "value": book.format.value.title(), "inline": True},
        {
            "name": "Release date",
            "value": book.release_date.isoformat() if book.release_date else "TBA",
            "inline": True,
        },
    ]
    if book.series:
        series = f"{book.series} #{book.series_sequence}" if book.series_sequence else book.series
        fields.append({"name": "Series", "value": series, "inline": True})

    embed: dict[str, Any] = {
        "title": book.title,
        "description": f"by {book.author.name}",
        "color": _EMBED_COLOR,
        "fields": fields,
    }
    if book.cover_url:
        embed["thumbnail"] = {"url": book.cover_url}
    return embed


def book_field(book: Book) -> dict[str, Any]:
    """Compact one-book field for grouping several books under a single digest embed."""
    name = book.title
    if book.series:
        if book.series_sequence:
            name += f" ({book.series} #{book.series_sequence})"
        else:
            name += f" ({book.series})"
    release = book.release_date.isoformat() if book.release_date else "TBA"
    return {
        "name": name[:256],
        "value": f"{book.author.name} · {release}"[:1024],
        "inline": False,
    }


def bucket_embeds(label: str, books: list[Book]) -> list[dict[str, Any]]:
    """One embed titled `label` per group of books, chunked to Discord's field/char limits."""
    embeds: list[dict[str, Any]] = []
    fields: list[dict[str, Any]] = []
    chars = len(label)

    for book in books:
        field = book_field(book)
        length = len(field["name"]) + len(field["value"])
        if fields and (len(fields) >= _MAX_FIELDS_PER_EMBED or chars + length > _MAX_EMBED_CHARS):
            embeds.append({"title": label, "color": _EMBED_COLOR, "fields": fields})
            fields = []
            chars = len(label)
        fields.append(field)
        chars += length

    if fields:
        embeds.append({"title": label, "color": _EMBED_COLOR, "fields": fields})

    return embeds


class DiscordNotifier:
    async def send(
        self, webhook_url: str, content: str = "", embeds: list[dict[str, Any]] | None = None
    ) -> None:
        payload: dict[str, Any] = {}
        if content:
            payload["content"] = content
        if embeds:
            payload["embeds"] = embeds
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(webhook_url, json=payload)
            response.raise_for_status()
