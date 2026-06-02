"""init

Revision ID: 0001
Revises:
Create Date: 2026-06-02

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "wb_accounts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("api_key", sa.Text),
        sa.Column("tax_type", sa.String(16), nullable=False, server_default="usn_6"),
        sa.Column("tax_rate", sa.Numeric(6, 4), nullable=False, server_default="0.06"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "reports",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("account_id", sa.Integer, sa.ForeignKey("wb_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source", sa.String(16), nullable=False),
        sa.Column("date_from", sa.Date, nullable=False),
        sa.Column("date_to", sa.Date, nullable=False),
        sa.Column("rows_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_reports_account_id", "reports", ["account_id"])

    op.create_table(
        "report_rows",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("report_id", sa.Integer, sa.ForeignKey("reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("account_id", sa.Integer, sa.ForeignKey("wb_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("realizationreport_id", sa.BigInteger),
        sa.Column("rrd_id", sa.BigInteger),
        sa.Column("nm_id", sa.BigInteger),
        sa.Column("subject_name", sa.String(255)),
        sa.Column("brand_name", sa.String(255)),
        sa.Column("sa_name", sa.String(255)),
        sa.Column("ts_name", sa.String(64)),
        sa.Column("barcode", sa.String(64)),
        sa.Column("doc_type_name", sa.String(64)),
        sa.Column("supplier_oper_name", sa.String(255)),
        sa.Column("order_dt", sa.DateTime),
        sa.Column("sale_dt", sa.DateTime),
        sa.Column("rr_dt", sa.Date),
        sa.Column("quantity", sa.Integer, nullable=False, server_default="0"),
        sa.Column("retail_price", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("retail_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("retail_price_withdisc_rub", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("ppvz_for_pay", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("ppvz_sales_commission", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("ppvz_reward", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("ppvz_vw", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("ppvz_vw_nds", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("acquiring_fee", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("delivery_rub", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("storage_fee", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("acceptance", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("penalty", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("additional_payment", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("deduction", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("rebill_logistic_cost", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.UniqueConstraint("account_id", "rrd_id", name="uq_account_rrd"),
    )
    op.create_index("ix_report_rows_report_id", "report_rows", ["report_id"])
    op.create_index("ix_report_rows_account_id", "report_rows", ["account_id"])
    op.create_index("ix_report_rows_nm_id", "report_rows", ["nm_id"])
    op.create_index("ix_report_rows_sa_name", "report_rows", ["sa_name"])
    op.create_index("ix_report_rows_rr_dt", "report_rows", ["rr_dt"])
    op.create_index("ix_report_rows_doc_type_name", "report_rows", ["doc_type_name"])
    op.create_index("ix_report_rows_supplier_oper_name", "report_rows", ["supplier_oper_name"])
    op.create_index("ix_report_rows_rrd_id", "report_rows", ["rrd_id"])
    op.create_index("ix_report_rows_realizationreport_id", "report_rows", ["realizationreport_id"])
    op.create_index("ix_rows_account_period", "report_rows", ["account_id", "rr_dt"])

    op.create_table(
        "cost_prices",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("account_id", sa.Integer, sa.ForeignKey("wb_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("nm_id", sa.BigInteger),
        sa.Column("sa_name", sa.String(255)),
        sa.Column("cost", sa.Numeric(14, 2), nullable=False),
        sa.Column("valid_from", sa.Date, nullable=False),
        sa.Column("valid_to", sa.Date),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_cost_prices_account_id", "cost_prices", ["account_id"])
    op.create_index("ix_cost_prices_nm_id", "cost_prices", ["nm_id"])
    op.create_index("ix_cost_prices_sa_name", "cost_prices", ["sa_name"])

    op.create_table(
        "expenses",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("account_id", sa.Integer, sa.ForeignKey("wb_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("date_from", sa.Date, nullable=False),
        sa.Column("date_to", sa.Date, nullable=False),
        sa.Column("comment", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_expenses_account_id", "expenses", ["account_id"])
    op.create_index("ix_expenses_date_from", "expenses", ["date_from"])
    op.create_index("ix_expenses_date_to", "expenses", ["date_to"])


def downgrade() -> None:
    op.drop_table("expenses")
    op.drop_table("cost_prices")
    op.drop_table("report_rows")
    op.drop_table("reports")
    op.drop_table("wb_accounts")
