"""Клиент WB Statistics API. Эндпоинт reportDetailByPeriod."""
from __future__ import annotations
from datetime import date
from typing import Any
import asyncio
import logging

import httpx

from ..config import settings


log = logging.getLogger("wb_api")


REPORT_PATH = "/api/v5/supplier/reportDetailByPeriod"


class WBApiError(RuntimeError):
    pass


class WBRateLimitError(WBApiError):
    pass


async def fetch_report_detail(
    api_key: str,
    date_from: date,
    date_to: date,
    *,
    limit: int = 100_000,
) -> list[dict[str, Any]]:
    """Постранично выгружает детализацию отчёта реализации.

    ВБ пагинирует через rrdid: каждый следующий запрос начинается с
    последнего rrd_id предыдущей страницы. Когда страница вернулась пустой —
    стоп.
    """
    headers = {"Authorization": api_key}
    params_base = {
        "dateFrom": date_from.isoformat(),
        "dateTo": date_to.isoformat(),
        "limit": limit,
    }
    rows: list[dict[str, Any]] = []
    rrdid = 0
    async with httpx.AsyncClient(
        base_url=settings.wb_api_base,
        timeout=settings.wb_api_timeout,
        headers=headers,
    ) as client:
        while True:
            params = {**params_base, "rrdid": rrdid}
            for attempt in range(5):
                try:
                    resp = await client.get(REPORT_PATH, params=params)
                except httpx.HTTPError as e:
                    log.warning("WB request failed (attempt %d): %s", attempt, e)
                    if attempt == 4:
                        raise WBApiError(f"Network error talking to WB: {e}")
                    await asyncio.sleep(2 ** attempt)
                    continue
                if resp.status_code == 429:
                    # ВБ лимит на этот endpoint — 1 запрос в минуту.
                    # Уважаем Retry-After если пришёл, иначе минимум 65 сек.
                    retry_after = resp.headers.get("Retry-After")
                    delay = max(int(retry_after), 65) if (retry_after and retry_after.isdigit()) else 65
                    log.info("WB 429 (attempt %d), waiting %ds", attempt, delay)
                    if attempt == 2:  # 2 попытки максимум (~2 минуты)
                        raise WBRateLimitError(
                            f"Лимит WB API исчерпан. Подождите {delay} сек и попробуйте снова."
                        )
                    await asyncio.sleep(delay)
                    continue
                if resp.status_code >= 400:
                    body = resp.text[:500]
                    log.error("WB API %d: %s", resp.status_code, body)
                    raise WBApiError(f"WB API {resp.status_code}: {body}")
                break
            else:
                raise WBApiError("WB API rate limit exceeded after 5 retries")

            page = resp.json() or []
            log.info("WB page rrdid=%s size=%d", rrdid, len(page))
            if not page:
                break
            rows.extend(page)
            rrdid = page[-1].get("rrd_id") or 0
            if not rrdid or len(page) < limit:
                break
            # ВБ держит 1 rps на этот endpoint — между страницами ждём.
            await asyncio.sleep(65)
    log.info("WB total rows: %d", len(rows))
    return rows
