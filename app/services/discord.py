import httpx


class DiscordNotifier:
    async def send(self, webhook_url: str, content: str) -> None:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(webhook_url, json={"content": content})
            response.raise_for_status()
