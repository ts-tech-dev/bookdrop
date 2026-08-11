from typing import Any

import httpx

from app.models import Book

# Discord's "blurple".
_EMBED_COLOR = 0x5865F2


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
