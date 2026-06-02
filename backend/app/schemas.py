from __future__ import annotations
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field


class AccountIn(BaseModel):
    name: str
    api_key: Optional[str] = None
    tax_type: str = "usn_income"  # usn_income | usn_expenses | none
    tax_rate: Decimal = Decimal("0.06")
    vat_rate: Decimal = Decimal("0")  # 0 | 0.05 | 0.07 | 0.20 | 0.22


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    api_key: Optional[str] = None
    tax_type: str
    tax_rate: Decimal
    vat_rate: Decimal
    created_at: datetime


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    account_id: int
    source: str
    date_from: date
    date_to: date
    rows_count: int
    created_at: datetime


class CostPriceIn(BaseModel):
    nm_id: Optional[int] = None
    sa_name: Optional[str] = None
    cost: Decimal
    valid_from: date


class CostPriceOut(CostPriceIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    valid_to: Optional[date]


class ExpenseIn(BaseModel):
    category: str
    amount: Decimal
    date_from: date
    date_to: date
    comment: Optional[str] = None


class ExpenseOut(ExpenseIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ProfitSummary(BaseModel):
    date_from: date
    date_to: date
    revenue: Decimal = Field(description="Выручка по retail_price_withdisc_rub")
    sales_qty: int
    returns_qty: int
    to_pay: Decimal = Field(description="Σ ppvz_for_pay — сумма к перечислению от ВБ")
    wb_commission: Decimal
    logistics: Decimal
    storage: Decimal
    acceptance: Decimal
    penalty: Decimal
    deduction: Decimal
    acquiring: Decimal
    rebill_logistic: Decimal
    additional_payment: Decimal
    cost_of_goods: Decimal
    vat: Decimal = Field(description="НДС к уплате (исходящий минус упрощённый вычет)")
    tax: Decimal = Field(description="УСН")
    external_expenses: Decimal
    net_profit: Decimal
    margin_pct: Decimal


class SkuProfitRow(BaseModel):
    nm_id: Optional[int]
    sa_name: Optional[str]
    subject_name: Optional[str]
    brand_name: Optional[str]
    title: Optional[str] = None
    photo_url: Optional[str] = None
    sales_qty: int
    returns_qty: int
    revenue: Decimal
    to_pay: Decimal
    wb_commission: Decimal
    logistics: Decimal
    storage: Decimal
    cost_of_goods: Decimal
    net_profit: Decimal
    margin_pct: Decimal


class WeeklyPoint(BaseModel):
    week_start: date
    revenue: Decimal
    to_pay: Decimal
    cost_of_goods: Decimal
    vat: Decimal
    tax: Decimal
    external_expenses: Decimal
    net_profit: Decimal


class ApiPullIn(BaseModel):
    account_id: int
    date_from: date
    date_to: date


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nm_id: int
    sa_name: Optional[str]
    title: Optional[str]
    brand: Optional[str]
    subject_name: Optional[str]
    photo_url: Optional[str]


class PeriodCompare(BaseModel):
    current: ProfitSummary
    previous: ProfitSummary
    delta_pct: dict[str, Optional[Decimal]]
