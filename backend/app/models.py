from __future__ import annotations
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    BigInteger, Date, DateTime, ForeignKey, Integer, Numeric, String, Text,
    UniqueConstraint, Index, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class WBAccount(Base):
    __tablename__ = "wb_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    api_key: Mapped[Optional[str]] = mapped_column(Text)
    # УСН: usn_income (доходы), usn_expenses (доходы−расходы), none
    tax_type: Mapped[str] = mapped_column(String(16), default="usn_income")
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(6, 4), default=Decimal("0.06"))
    # НДС: 0 / 0.05 / 0.07 / 0.20 / 0.22
    vat_rate: Mapped[Decimal] = mapped_column(Numeric(6, 4), default=Decimal("0"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    reports: Mapped[list["Report"]] = relationship(back_populates="account", cascade="all,delete")
    cost_prices: Mapped[list["CostPrice"]] = relationship(back_populates="account", cascade="all,delete")
    expenses: Mapped[list["Expense"]] = relationship(back_populates="account", cascade="all,delete")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("wb_accounts.id", ondelete="CASCADE"), index=True)
    source: Mapped[str] = mapped_column(String(16))  # api | excel
    date_from: Mapped[date] = mapped_column(Date)
    date_to: Mapped[date] = mapped_column(Date)
    rows_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    account: Mapped["WBAccount"] = relationship(back_populates="reports")
    rows: Mapped[list["ReportRow"]] = relationship(back_populates="report", cascade="all,delete")


class ReportRow(Base):
    """Одна строка детализации еженедельного отчёта реализации."""
    __tablename__ = "report_rows"

    id: Mapped[int] = mapped_column(primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id", ondelete="CASCADE"), index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("wb_accounts.id", ondelete="CASCADE"), index=True)

    realizationreport_id: Mapped[Optional[int]] = mapped_column(BigInteger, index=True)
    rrd_id: Mapped[Optional[int]] = mapped_column(BigInteger, index=True)
    nm_id: Mapped[Optional[int]] = mapped_column(BigInteger, index=True)
    subject_name: Mapped[Optional[str]] = mapped_column(String(255))
    brand_name: Mapped[Optional[str]] = mapped_column(String(255))
    sa_name: Mapped[Optional[str]] = mapped_column(String(255), index=True)  # supplier article
    ts_name: Mapped[Optional[str]] = mapped_column(String(64))  # size
    barcode: Mapped[Optional[str]] = mapped_column(String(64))

    doc_type_name: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    supplier_oper_name: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    order_dt: Mapped[Optional[datetime]] = mapped_column(DateTime)
    sale_dt: Mapped[Optional[datetime]] = mapped_column(DateTime)
    rr_dt: Mapped[Optional[date]] = mapped_column(Date, index=True)

    quantity: Mapped[int] = mapped_column(Integer, default=0)
    retail_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    retail_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    retail_price_withdisc_rub: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)

    ppvz_for_pay: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    ppvz_sales_commission: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    ppvz_reward: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    ppvz_vw: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    ppvz_vw_nds: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    acquiring_fee: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)

    delivery_rub: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    storage_fee: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    acceptance: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    penalty: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    additional_payment: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    deduction: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    rebill_logistic_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)

    report: Mapped["Report"] = relationship(back_populates="rows")

    __table_args__ = (
        UniqueConstraint("account_id", "rrd_id", name="uq_account_rrd"),
        Index("ix_rows_account_period", "account_id", "rr_dt"),
    )


class CostPrice(Base):
    """Себестоимость SKU. Версионная: valid_from/valid_to (NULL = текущая)."""
    __tablename__ = "cost_prices"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("wb_accounts.id", ondelete="CASCADE"), index=True)
    nm_id: Mapped[Optional[int]] = mapped_column(BigInteger, index=True)
    sa_name: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    cost: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    valid_from: Mapped[date] = mapped_column(Date)
    valid_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    account: Mapped["WBAccount"] = relationship(back_populates="cost_prices")


class Expense(Base):
    """Внешние расходы: ФОТ, реклама вне ВБ, упаковка, и т.п."""
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("wb_accounts.id", ondelete="CASCADE"), index=True)
    category: Mapped[str] = mapped_column(String(64))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    date_from: Mapped[date] = mapped_column(Date, index=True)
    date_to: Mapped[date] = mapped_column(Date, index=True)
    comment: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    account: Mapped["WBAccount"] = relationship(back_populates="expenses")
