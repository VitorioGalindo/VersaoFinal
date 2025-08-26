"""make ticker company_id nullable

Revision ID: 5a6c7d8e9f10
Revises: 0f54de82af65
Create Date: 2025-08-12 15:37:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '5a6c7d8e9f10'
down_revision: Union[str, Sequence[str], None] = '0f54de82af65'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Make company_id nullable in a SQLite-compatible way."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "tickers" not in inspector.get_table_names():
        return
    with op.batch_alter_table("tickers") as batch_op:
        batch_op.alter_column(
            "company_id", existing_type=sa.Integer(), nullable=True
        )


def downgrade() -> None:
    """Revert company_id back to non-nullable."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "tickers" not in inspector.get_table_names():
        return
    with op.batch_alter_table("tickers") as batch_op:
        batch_op.alter_column(
            "company_id", existing_type=sa.Integer(), nullable=False
        )
