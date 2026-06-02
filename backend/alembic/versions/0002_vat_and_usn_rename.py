"""add vat_rate; rename tax_type values

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-02

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "wb_accounts",
        sa.Column("vat_rate", sa.Numeric(6, 4), nullable=False, server_default="0"),
    )
    op.alter_column(
        "wb_accounts", "tax_type",
        existing_type=sa.String(16),
        server_default="usn_income",
    )
    op.execute("UPDATE wb_accounts SET tax_type='usn_income'  WHERE tax_type='usn_6'")
    op.execute("UPDATE wb_accounts SET tax_type='usn_expenses' WHERE tax_type='usn_15'")


def downgrade() -> None:
    op.execute("UPDATE wb_accounts SET tax_type='usn_15' WHERE tax_type='usn_expenses'")
    op.execute("UPDATE wb_accounts SET tax_type='usn_6'  WHERE tax_type='usn_income'")
    op.alter_column(
        "wb_accounts", "tax_type",
        existing_type=sa.String(16),
        server_default="usn_6",
    )
    op.drop_column("wb_accounts", "vat_rate")
