"""Клиент WB Statistics API. Эндпоинт reportDetailByPeriod."""
from __future__ import annotations
from datetime import date
from typing import Any
import asyncio

import httpx

from ..config import settings


REPORT_PATH = "/api/v5/supplier/reportDetailByPeriod"


class WBApiError(RuntimeError):
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
                resp = await client.get(REPORT_PATH, params=params)
                if resp.status_code == 429:
                    await asyncio.sleep(2 ** attempt)
                    continue
                if resp.status_code >= 400:
                    raise WBApiError(f"WB API {resp.status_code}: {resp.text[:300]}")
                break
            else:
                raise WBApiError("WB API rate limit exceeded")

            page = resp.json() or []
            if not page:
                break
            rows.extend(page)
            rrdid = page[-1].get("rrd_id") or 0
            if not rrdid or len(page) < limit:
                break
    return rows
