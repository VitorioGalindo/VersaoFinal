"""add portfolio daily metrics

Revision ID: 41040a87193c
Revises: 3bba235f3ec0
Create Date: 2025-08-12 20:52:00.291975
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "41040a87193c"
down_revision: Union[str, Sequence[str], None] = "3bba235f3ec0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "portfolios",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
    )
    op.create_table(
        "portfolio_daily_metrics",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("portfolio_id", sa.Integer(), nullable=False),
        sa.Column("metric_id", sa.String(length=100), nullable=False),
        sa.Column("value", sa.Numeric(20, 4), nullable=False),
        sa.Column(
            "date", sa.Date(), nullable=False, server_default=sa.text("(CURRENT_DATE)")
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"]),
        sa.UniqueConstraint(
            "portfolio_id", "metric_id", "date", name="uix_portfolio_metric_date"
        ),
    )
    op.create_index(
        "ix_portfolio_daily_metrics_portfolio_id",
        "portfolio_daily_metrics",
        ["portfolio_id"],
    )
    op.create_table(
        "portfolio_daily_values",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("portfolio_id", sa.Integer(), nullable=False),
        sa.Column(
            "date", sa.Date(), nullable=False, server_default=sa.text("(CURRENT_DATE)")
        ),
        sa.Column("total_value", sa.Numeric(20, 2), nullable=False),
        sa.Column("total_cost", sa.Numeric(20, 2), nullable=False),
        sa.Column("total_gain", sa.Numeric(20, 2), nullable=False),
        sa.Column("total_gain_percent", sa.Numeric(10, 4), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"]),
        sa.UniqueConstraint("portfolio_id", "date", name="uix_portfolio_date"),
    )
    op.create_index(
        "ix_portfolio_daily_values_portfolio_id",
        "portfolio_daily_values",
        ["portfolio_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_portfolio_daily_values_portfolio_id", table_name="portfolio_daily_values"
    )
    op.drop_table("portfolio_daily_values")
    op.drop_index(
        "ix_portfolio_daily_metrics_portfolio_id", table_name="portfolio_daily_metrics"
    )
    op.drop_table("portfolio_daily_metrics")
    op.drop_table("portfolios")
