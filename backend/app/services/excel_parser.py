"""Парсер Excel-выгрузки еженедельного отчёта реализации ВБ.

Маппинг колонок сверен с реальной выгрузкой ЛК ВБ (82 колонки, 2026).
"""
from __future__ import annotations
from io import BytesIO
from typing import Any

import pandas as pd


# Ключ — нормализованное имя колонки (lower, только буквы/цифры),
# значение — служебное имя поля (как у WB API).
RUS_TO_API: dict[str, str] = {
    # Идентификация
    "номерпоставки": "supplier_contract_code",
    "предмет": "subject_name",
    "кодноменклатуры": "nm_id",
    "артикулwb": "nm_id",
    "бренд": "brand_name",
    "артикулпоставщика": "sa_name",
    "название": "product_name",
    "размер": "ts_name",
    "баркод": "barcode",
    "штрихкод": "barcode",
    # Операция
    "типдокумента": "doc_type_name",
    "обоснованиедляоплаты": "supplier_oper_name",
    "датазаказапокупателем": "order_dt",
    "датапродажи": "sale_dt",
    # Количества
    "колво": "quantity",
    "количестводоставок": "delivery_amount",
    "количествовозврата": "return_amount",
    # Цены/выручка
    "ценарозничная": "retail_price",
    "вайлдберризреализовалтоварпр": "retail_amount",
    "ценарозничнаясучетомсогласованнойскидки": "retail_price_withdisc_rub",
    # Вознаграждения/комиссии
    "вознаграждениеспродаждовычетауслугповеренногобезндс": "ppvz_sales_commission",
    "возмещениезавыдачуивозвраттоваровнапвз": "ppvz_reward",
    "компенсацияплатежныхуслугкомиссиязаинтеграциюплатежныхсервисов": "acquiring_fee",
    "вознаграждениевайлдберризввбезндс": "ppvz_vw",
    "ндссвознаграждениявайлдберриз": "ppvz_vw_nds",
    "кперечислениюпродавцузареализованныйтовар": "ppvz_for_pay",
    # Логистика/хранение/прочее
    "услугиподоставкетоварапокупателю": "delivery_rub",
    "общаясуммаштрафов": "penalty",
    "корректировкавознаграждениявайлдберризвв": "additional_payment",
    "хранение": "storage_fee",
    "удержания": "deduction",
    "операциинаприемке": "acceptance",
    "возмещениеиздержекпоперевозкепоскладскимоперациямстоваром": "rebill_logistic_cost",
    "организаторперевозки": "rebill_logistic_org",
    # Метаданные
    "стикермп": "sticker_id",
    "наименованиебанкаэквайера": "acquiring_bank",
    "номерофиса": "ppvz_office_id",
    "наименованиеофисадоставки": "ppvz_office_name",
    "иннпартнера": "ppvz_inn",
    "партнер": "ppvz_supplier_name",
    "склад": "office_name",
    "страна": "site_country",
    "типкоробов": "gi_box_type_name",
    "srid": "srid",
    "шк": "shk_id",
}

NUMERIC_FIELDS = {
    "quantity", "delivery_amount", "return_amount",
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
    """Читает .xlsx и возвращает список словарей в формате API."""
    xl = pd.ExcelFile(BytesIO(content))
    df = xl.parse(xl.sheet_names[0])

    rename: dict[str, str] = {}
    for col in df.columns:
        key = _norm(col)
        if key in RUS_TO_API:
            rename[col] = RUS_TO_API[key]
    df = df.rename(columns=rename)

    keep = [c for c in df.columns if c in set(RUS_TO_API.values())]
    df = df[keep].copy()

    for c in NUMERIC_FIELDS & set(df.columns):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in DATETIME_FIELDS & set(df.columns):
        df[c] = pd.to_datetime(df[c], errors="coerce")
    for c in DATE_FIELDS & set(df.columns):
        df[c] = pd.to_datetime(df[c], errors="coerce").dt.date

    df = df.where(pd.notnull(df), None)
    records = df.to_dict(orient="records")

    # В Excel нет rrd_id / rr_dt — генерим из индекса и sale_dt.
    for idx, rec in enumerate(records, start=1):
        if rec.get("rrd_id") is None:
            rec["rrd_id"] = -idx  # отрицательные = синтетические, не пересекаются с API
        if rec.get("rr_dt") is None:
            d = rec.get("sale_dt") or rec.get("order_dt")
            if d is not None:
                rec["rr_dt"] = d.date() if hasattr(d, "date") else d
    return records
