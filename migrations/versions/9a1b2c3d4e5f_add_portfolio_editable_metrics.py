"""add portfolio editable metrics table

Revision ID: 9a1b2c3d4e5f
Revises: 41040a87193c
Create Date: 2025-08-18 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a1b2c3d4e5f'
down_revision: Union[str, Sequence[str], None] = '41040a87193c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "portfolio_editable_metrics",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("portfolio_id", sa.Integer(), nullable=False),
        sa.Column("metric_key", sa.String(length=100), nullable=False),
        sa.Column("metric_value", sa.Numeric(20, 4), nullable=False),
        sa.Column(
            "date", sa.Date(), nullable=False, server_default=sa.text("(CURRENT_DATE)")
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"]),
        sa.UniqueConstraint(
            "portfolio_id", "metric_key", "date", name="uix_portfolio_editable_metric_date"
        ),
    )
    op.create_index(
        "idx_portfolio_editable_metrics_portfolio_id",
        "portfolio_editable_metrics",
        ["portfolio_id"],
    )
    op.create_index(
        "idx_portfolio_editable_metrics_date",
        "portfolio_editable_metrics",
        ["date"],
    )


def downgrade() -> None:
    op.drop_index(
        "idx_portfolio_editable_metrics_date", table_name="portfolio_editable_metrics"
    )
    op.drop_index(
        "idx_portfolio_editable_metrics_portfolio_id", table_name="portfolio_editable_metrics"
    )
    op.drop_table("portfolio_editable_metrics")