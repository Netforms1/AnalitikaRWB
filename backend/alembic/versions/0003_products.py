"""products table

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-02

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("account_id", sa.Integer, sa.ForeignKey("wb_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("nm_id", sa.BigInteger, nullable=False),
        sa.Column("sa_name", sa.String(255)),
        sa.Column("title", sa.String(512)),
        sa.Column("brand", sa.String(255)),
        sa.Column("subject_name", sa.String(255)),
        sa.Column("photo_url", sa.Text),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("account_id", "nm_id", name="uq_account_nm"),
    )
    op.create_index("ix_products_account_id", "products", ["account_id"])
    op.create_index("ix_products_nm_id", "products", ["nm_id"])
    op.create_index("ix_products_sa_name", "products", ["sa_name"])


def downgrade() -> None:
    op.drop_table("products")
