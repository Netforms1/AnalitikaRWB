"""Расчёт чистой прибыли по строкам отчёта реализации ВБ.

Формула:
    Чистая прибыль = К перечислению − Себестоимость − Налог − Прочие расходы
"""
from __future__ import annotations
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from .. import models, schemas


ZERO = Decimal("0")


def _pct(num: Decimal, denom: Decimal) -> Decimal:
    if not denom:
        return ZERO
    return (num / denom * Decimal("100")).quantize(Decimal("0.01"))


def _cost_for_nm(db: Session, account_id: int, nm_id: Optional[int], sa_name: Optional[str], at: date) -> Decimal:
    """Возвращает себестоимость на дату at. Версии по valid_from/valid_to."""
    if nm_id is None and not sa_name:
        return ZERO
    q = select(models.CostPrice).where(
        models.CostPrice.account_id == account_id,
        models.CostPrice.valid_from <= at,
        (models.CostPrice.valid_to.is_(None)) | (models.CostPrice.valid_to >= at),
    )
    if nm_id is not None:
        q = q.where(models.CostPrice.nm_id == nm_id)
    elif sa_name:
        q = q.where(models.CostPrice.sa_name == sa_name)
    q = q.order_by(models.CostPrice.valid_from.desc())
    row = db.execute(q).scalars().first()
    return row.cost if row else ZERO


def compute_summary(
    db: Session,
    account_id: int,
    date_from: date,
    date_to: date,
) -> schemas.ProfitSummary:
    account = db.get(models.WBAccount, account_id)
    if account is None:
        raise ValueError("Account not found")

    rows = db.execute(
        select(models.ReportRow).where(
            models.ReportRow.account_id == account_id,
            models.ReportRow.rr_dt >= date_from,
            models.ReportRow.rr_dt <= date_to,
        )
    ).scalars().all()

    revenue = ZERO
    sales_qty = 0
    returns_qty = 0
    to_pay = ZERO
    commission = ZERO
    logistics = ZERO
    storage = ZERO
    acceptance = ZERO
    penalty = ZERO
    deduction = ZERO
    acquiring = ZERO
    rebill = ZERO
    addpay = ZERO
    cog = ZERO

    for r in rows:
        op = (r.supplier_oper_name or "").lower()
        is_sale = "продажа" in op
        is_return = "возврат" in op
        qty = r.quantity or 0
        price = r.retail_price_withdisc_rub or ZERO
        if is_sale:
            revenue += price
            sales_qty += qty
        elif is_return:
            revenue -= price
            returns_qty += qty
        to_pay += r.ppvz_for_pay or ZERO
        commission += r.ppvz_sales_commission or ZERO
        logistics += r.delivery_rub or ZERO
        storage += r.storage_fee or ZERO
        acceptance += r.acceptance or ZERO
        penalty += r.penalty or ZERO
        deduction += r.deduction or ZERO
        acquiring += r.acquiring_fee or ZERO
        rebill += r.rebill_logistic_cost or ZERO
        addpay += r.additional_payment or ZERO

        unit_cost = _cost_for_nm(db, account_id, r.nm_id, r.sa_name, r.rr_dt or date_to)
        if is_sale:
            cog += unit_cost * qty
        elif is_return:
            cog -= unit_cost * qty

    # Налог
    tax_base = ZERO
    if account.tax_type == "usn_6":
        tax_base = revenue
    elif account.tax_type == "usn_15":
        # «доходы минус расходы» — упрощённо: К перечислению минус себестоимость
        tax_base = max(to_pay - cog, ZERO)
    tax = (tax_base * (account.tax_rate or ZERO)).quantize(Decimal("0.01"))

    # Внешние расходы за период
    ext = db.execute(
        select(func.coalesce(func.sum(models.Expense.amount), 0)).where(
            models.Expense.account_id == account_id,
            models.Expense.date_from <= date_to,
            models.Expense.date_to >= date_from,
        )
    ).scalar_one() or ZERO
    ext = Decimal(str(ext))

    net = (to_pay - cog - tax - ext).quantize(Decimal("0.01"))
    return schemas.ProfitSummary(
        date_from=date_from, date_to=date_to,
        revenue=revenue.quantize(Decimal("0.01")),
        sales_qty=sales_qty, returns_qty=returns_qty,
        to_pay=to_pay.quantize(Decimal("0.01")),
        wb_commission=commission.quantize(Decimal("0.01")),
        logistics=logistics.quantize(Decimal("0.01")),
        storage=storage.quantize(Decimal("0.01")),
        acceptance=acceptance.quantize(Decimal("0.01")),
        penalty=penalty.quantize(Decimal("0.01")),
        deduction=deduction.quantize(Decimal("0.01")),
        acquiring=acquiring.quantize(Decimal("0.01")),
        rebill_logistic=rebill.quantize(Decimal("0.01")),
        additional_payment=addpay.quantize(Decimal("0.01")),
        cost_of_goods=cog.quantize(Decimal("0.01")),
        tax=tax,
        external_expenses=ext.quantize(Decimal("0.01")),
        net_profit=net,
        margin_pct=_pct(net, revenue),
    )


def compute_by_sku(
    db: Session, account_id: int, date_from: date, date_to: date,
) -> list[schemas.SkuProfitRow]:
    rows = db.execute(
        select(models.ReportRow).where(
            models.ReportRow.account_id == account_id,
            models.ReportRow.rr_dt >= date_from,
            models.ReportRow.rr_dt <= date_to,
        )
    ).scalars().all()

    bucket: dict[tuple, dict] = {}
    for r in rows:
        key = (r.nm_id, r.sa_name)
        b = bucket.setdefault(key, {
            "nm_id": r.nm_id, "sa_name": r.sa_name,
            "subject_name": r.subject_name, "brand_name": r.brand_name,
            "sales_qty": 0, "returns_qty": 0,
            "revenue": ZERO, "to_pay": ZERO, "commission": ZERO,
            "logistics": ZERO, "storage": ZERO, "cog": ZERO,
        })
        op = (r.supplier_oper_name or "").lower()
        is_sale = "продажа" in op
        is_return = "возврат" in op
        qty = r.quantity or 0
        price = r.retail_price_withdisc_rub or ZERO
        if is_sale:
            b["revenue"] += price
            b["sales_qty"] += qty
        elif is_return:
            b["revenue"] -= price
            b["returns_qty"] += qty
        b["to_pay"] += r.ppvz_for_pay or ZERO
        b["commission"] += r.ppvz_sales_commission or ZERO
        b["logistics"] += r.delivery_rub or ZERO
        b["storage"] += r.storage_fee or ZERO
        unit_cost = _cost_for_nm(db, account_id, r.nm_id, r.sa_name, r.rr_dt or date_to)
        if is_sale:
            b["cog"] += unit_cost * qty
        elif is_return:
            b["cog"] -= unit_cost * qty

    out: list[schemas.SkuProfitRow] = []
    for b in bucket.values():
        net = b["to_pay"] - b["cog"]
        out.append(schemas.SkuProfitRow(
            nm_id=b["nm_id"], sa_name=b["sa_name"],
            subject_name=b["subject_name"], brand_name=b["brand_name"],
            sales_qty=b["sales_qty"], returns_qty=b["returns_qty"],
            revenue=b["revenue"].quantize(Decimal("0.01")),
            to_pay=b["to_pay"].quantize(Decimal("0.01")),
            wb_commission=b["commission"].quantize(Decimal("0.01")),
            logistics=b["logistics"].quantize(Decimal("0.01")),
            storage=b["storage"].quantize(Decimal("0.01")),
            cost_of_goods=b["cog"].quantize(Decimal("0.01")),
            net_profit=net.quantize(Decimal("0.01")),
            margin_pct=_pct(net, b["revenue"]),
        ))
    out.sort(key=lambda x: x.net_profit, reverse=True)
    return out


def compute_weekly(
    db: Session, account_id: int, date_from: date, date_to: date,
) -> list[schemas.WeeklyPoint]:
    """Группирует по ISO-неделе (понедельник)."""
    rows = db.execute(
        select(models.ReportRow).where(
            models.ReportRow.account_id == account_id,
            models.ReportRow.rr_dt >= date_from,
            models.ReportRow.rr_dt <= date_to,
        )
    ).scalars().all()

    account = db.get(models.WBAccount, account_id)
    weeks: dict[date, dict] = defaultdict(lambda: {
        "revenue": ZERO, "to_pay": ZERO, "cog": ZERO,
    })
    for r in rows:
        d = r.rr_dt or date_to
        wk = d - timedelta(days=d.weekday())
        b = weeks[wk]
        op = (r.supplier_oper_name or "").lower()
        is_sale = "продажа" in op
        is_return = "возврат" in op
        qty = r.quantity or 0
        price = r.retail_price_withdisc_rub or ZERO
        if is_sale:
            b["revenue"] += price
        elif is_return:
            b["revenue"] -= price
        b["to_pay"] += r.ppvz_for_pay or ZERO
        unit_cost = _cost_for_nm(db, account_id, r.nm_id, r.sa_name, d)
        if is_sale:
            b["cog"] += unit_cost * qty
        elif is_return:
            b["cog"] -= unit_cost * qty

    points: list[schemas.WeeklyPoint] = []
    for wk in sorted(weeks):
        b = weeks[wk]
        wk_end = wk + timedelta(days=6)
        if account.tax_type == "usn_6":
            tax = (b["revenue"] * (account.tax_rate or ZERO)).quantize(Decimal("0.01"))
        elif account.tax_type == "usn_15":
            tax = (max(b["to_pay"] - b["cog"], ZERO) * (account.tax_rate or ZERO)).quantize(Decimal("0.01"))
        else:
            tax = ZERO
        ext = db.execute(
            select(func.coalesce(func.sum(models.Expense.amount), 0)).where(
                models.Expense.account_id == account_id,
                models.Expense.date_from <= wk_end,
                models.Expense.date_to >= wk,
            )
        ).scalar_one() or ZERO
        ext = Decimal(str(ext))
        net = b["to_pay"] - b["cog"] - tax - ext
        points.append(schemas.WeeklyPoint(
            week_start=wk,
            revenue=b["revenue"].quantize(Decimal("0.01")),
            to_pay=b["to_pay"].quantize(Decimal("0.01")),
            cost_of_goods=b["cog"].quantize(Decimal("0.01")),
            tax=tax,
            external_expenses=ext.quantize(Decimal("0.01")),
            net_profit=net.quantize(Decimal("0.01")),
        ))
    return points
