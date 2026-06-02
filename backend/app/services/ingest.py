"""Сохранение строк отчёта в БД (upsert по (account_id, rrd_id))."""
from __future__ import annotations
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Iterable

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from .. import models


_NUMERIC_DEFAULTS = (
    "quantity",
    "retail_price", "retail_amount", "retail_price_withdisc_rub",
    "ppvz_for_pay", "ppvz_sales_commission", "ppvz_reward",
    "ppvz_vw", "ppvz_vw_nds", "acquiring_fee",
    "delivery_rub", "storage_fee", "acceptance",
    "penalty", "additional_payment", "deduction", "rebill_logistic_cost",
)


def _coerce_row(account_id: int, report_id: int, src: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {"account_id": account_id, "report_id": report_id}
    for k in (
        "realizationreport_id", "rrd_id", "nm_id",
        "subject_name", "brand_name", "sa_name", "ts_name", "barcode",
        "doc_type_name", "supplier_oper_name",
        "order_dt", "sale_dt", "rr_dt",
        *_NUMERIC_DEFAULTS,
    ):
        out[k] = src.get(k)
    for k in _NUMERIC_DEFAULTS:
        v = out.get(k)
        out[k] = Decimal(str(v)) if v not in (None, "") else Decimal("0")
    out["quantity"] = int(out["quantity"])
    # date/datetime sanity
    for k in ("order_dt", "sale_dt"):
        v = out.get(k)
        if isinstance(v, str) and v:
            try:
                out[k] = datetime.fromisoformat(v.replace("Z", "+00:00"))
            except ValueError:
                out[k] = None
    v = out.get("rr_dt")
    if isinstance(v, datetime):
        out["rr_dt"] = v.date()
    elif isinstance(v, str) and v:
        try:
            out["rr_dt"] = date.fromisoformat(v[:10])
        except ValueError:
            out["rr_dt"] = None
    return out


def ingest_rows(
    db: Session,
    account_id: int,
    source: str,
    date_from: date,
    date_to: date,
    rows: Iterable[dict[str, Any]],
) -> models.Report:
    rows = list(rows)
    report = models.Report(
        account_id=account_id,
        source=source,
        date_from=date_from,
        date_to=date_to,
        rows_count=len(rows),
    )
    db.add(report)
    db.flush()  # need report.id

    if not rows:
        db.commit()
        return report

    payload = [_coerce_row(account_id, report.id, r) for r in rows if r.get("rrd_id")]
    if not payload:
        report.rows_count = 0
        db.commit()
        return report

    # Дедуп по (account_id, rrd_id): ON CONFLICT не может дважды обновить ту же строку
    # в одном INSERT. При коллизии берём последнюю запись.
    dedup: dict[tuple, dict] = {}
    for row in payload:
        dedup[(row["account_id"], row["rrd_id"])] = row
    payload = list(dedup.values())

    # Postgres ограничивает один запрос 65535 параметрами. Режем на батчи.
    cols_per_row = len(payload[0])
    batch_size = max(1, 60000 // cols_per_row)
    inserted = 0
    for start in range(0, len(payload), batch_size):
        chunk = payload[start:start + batch_size]
        stmt = insert(models.ReportRow).values(chunk)
        update_cols = {c.name: c for c in stmt.excluded if c.name not in ("id", "account_id", "rrd_id")}
        stmt = stmt.on_conflict_do_update(constraint="uq_account_rrd", set_=update_cols)
        db.execute(stmt)
        inserted += len(chunk)

    report.rows_count = inserted
    db.commit()
    db.refresh(report)
    return report
