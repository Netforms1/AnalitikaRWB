"""Парсер Excel-выгрузки еженедельного отчёта реализации ВБ.

Колонки в ЛК ВБ выгружаются на русском. Маппим их в служебные имена,
совпадающие с API (snake_case).
"""
from __future__ import annotations
from io import BytesIO
from typing import Any

import pandas as pd


# Минимальный набор колонок, который используется в расчёте.
# Ключ — нормализованное имя колонки в Excel (lower, без пробелов и знаков),
# значение — служебное имя.
RUS_TO_API = {
    "номеротчёта": "realizationreport_id",
    "номеротчета": "realizationreport_id",
    "уникальныйid": "rrd_id",
    "артикулwb": "nm_id",
    "артикулпоставщика": "sa_name",
    "артикулпродавца": "sa_name",
    "предмет": "subject_name",
    "бренд": "brand_name",
    "размер": "ts_name",
    "штрихкод": "barcode",
    "типдокумента": "doc_type_name",
    "обоснованиедляоплаты": "supplier_oper_name",
    "датазаказа": "order_dt",
    "датапродажи": "sale_dt",
    "датаоперации": "rr_dt",
    "количество": "quantity",
    "ценарозничная": "retail_price",
    "сумкупродажвозвратов": "retail_amount",
    "ценарозничнаясучётомсогласованнойскидки": "retail_price_withdisc_rub",
    "квыплате": "ppvz_for_pay",
    "вознаграждениезаэквайрингзачётназначениеплатежа": "acquiring_fee",
    "размерэквайринга": "acquiring_fee",
    "вознаграждениеwbбезндс": "ppvz_vw",
    "ндссвознагражденияwb": "ppvz_vw_nds",
    "сборзалогистику": "delivery_rub",
    "стоимостьлогистики": "delivery_rub",
    "хранение": "storage_fee",
    "стоимостьхранения": "storage_fee",
    "платнаяприёмка": "acceptance",
    "приёмка": "acceptance",
    "штрафы": "penalty",
    "доплаты": "additional_payment",
    "удержания": "deduction",
    "прочиеудержаниявыплаты": "deduction",
    "возмещениеиздержекполистике": "rebill_logistic_cost",
    "комиссияwb": "ppvz_sales_commission",
}

NUMERIC_FIELDS = {
    "quantity",
    "retail_price", "retail_amount", "retail_price_withdisc_rub",
    "ppvz_for_pay", "ppvz_sales_commission", "ppvz_reward",
    "ppvz_vw", "ppvz_vw_nds", "acquiring_fee",
    "delivery_rub", "storage_fee", "acceptance",
    "penalty", "additional_payment", "deduction",
    "rebill_logistic_cost",
    "nm_id", "rrd_id", "realizationreport_id",
}

DATETIME_FIELDS = {"order_dt", "sale_dt"}
DATE_FIELDS = {"rr_dt"}


def _norm(s: str) -> str:
    return "".join(ch for ch in str(s).lower() if ch.isalnum())


def parse_report_excel(content: bytes) -> list[dict[str, Any]]:
    """Читает .xlsx и возвращает список словарей в формате как у API."""
    xl = pd.ExcelFile(BytesIO(content))
    # Берём первый лист
    df = xl.parse(xl.sheet_names[0])
    rename: dict[str, str] = {}
    for col in df.columns:
        key = _norm(col)
        if key in RUS_TO_API:
            rename[col] = RUS_TO_API[key]
    df = df.rename(columns=rename)
    # Оставляем только известные нам колонки
    keep = [c for c in df.columns if c in set(RUS_TO_API.values())]
    df = df[keep]

    for c in NUMERIC_FIELDS & set(df.columns):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in DATETIME_FIELDS & set(df.columns):
        df[c] = pd.to_datetime(df[c], errors="coerce")
    for c in DATE_FIELDS & set(df.columns):
        df[c] = pd.to_datetime(df[c], errors="coerce").dt.date

    df = df.where(pd.notnull(df), None)
    return df.to_dict(orient="records")
