"""users + wb_accounts.user_id

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-02

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.add_column(
        "wb_accounts",
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
    )

    # Если в БД уже есть магазины — создаём системного пользователя
    # и привязываем их все к нему. После апгрейда зарегистрируйте свой email
    # и админ-скриптом перенесите.
    bind = op.get_bind()
    has_accounts = bind.execute(sa.text("SELECT 1 FROM wb_accounts LIMIT 1")).first()
    if has_accounts:
        # bcrypt-хеш пароля "changeme" (сгенерирован один раз)
        bind.execute(sa.text(
            "INSERT INTO users (email, password_hash) "
            "VALUES ('legacy@local', "
            "'$2b$12$8hwfb04NaqACOb2izFsbIuX8CC1kdEg80.TZcdvrDnZ5Zhw6Smyja')"
        ))
        legacy_id = bind.execute(sa.text(
            "SELECT id FROM users WHERE email='legacy@local'"
        )).scalar_one()
        bind.execute(sa.text(
            f"UPDATE wb_accounts SET user_id={legacy_id} WHERE user_id IS NULL"
        ))

    op.alter_column("wb_accounts", "user_id", nullable=False)
    op.create_index("ix_wb_accounts_user_id", "wb_accounts", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_wb_accounts_user_id", "wb_accounts")
    op.drop_column("wb_accounts", "user_id")
    op.drop_index("ix_users_email", "users")
    op.drop_table("users")
