"""Клиент WB Content API. Подтягивает карточки товаров (cards/list)."""
from __future__ import annotations
import asyncio
import logging
from typing import Any

import httpx


CONTENT_BASE = "https://content-api.wildberries.ru"
CARDS_LIST_PATH = "/content/v2/get/cards/list"

log = logging.getLogger("wb_content")


class WBContentError(RuntimeError):
    pass


async def fetch_all_cards(api_key: str, *, limit: int = 100) -> list[dict[str, Any]]:
    """Все карточки через курсорную пагинацию.

    Content API лимит ≈ 100 запросов в минуту — пагинацию проходим без пауз.
    """
    headers = {"Authorization": api_key, "Content-Type": "application/json"}
    cursor: dict[str, Any] = {"limit": limit}
    out: list[dict[str, Any]] = []

    async with httpx.AsyncClient(base_url=CONTENT_BASE, timeout=60, headers=headers) as client:
        while True:
            body = {
                "settings": {
                    "sort": {"ascending": True},
                    "cursor": cursor,
                    "filter": {"withPhoto": -1},
                }
            }
            for attempt in range(3):
                resp = await client.post(CARDS_LIST_PATH, json=body)
                if resp.status_code == 429:
                    await asyncio.sleep(5 * (attempt + 1))
                    continue
                if resp.status_code >= 400:
                    raise WBContentError(f"Content API {resp.status_code}: {resp.text[:300]}")
                break
            else:
                raise WBContentError("Content API rate limit")

            data = resp.json() or {}
            cards = data.get("cards") or []
            cur = data.get("cursor") or {}
            log.info("cards page: %d (total cursor=%s)", len(cards), cur.get("total"))
            out.extend(cards)
            total = cur.get("total", 0)
            if total < limit:
                break
            cursor = {
                "limit": limit,
                "updatedAt": cur.get("updatedAt"),
                "nmID": cur.get("nmID"),
            }
    return out


def card_photo_url(card: dict[str, Any]) -> str | None:
    """Берёт URL миниатюры из карточки (поле photos[0].c246x328 / big / tm)."""
    photos = card.get("photos") or []
    if not photos:
        return None
    p = photos[0]
    return p.get("c246x328") or p.get("tm") or p.get("big") or p.get("square")
