"""add macro indicator tables

Revision ID: 86904b35ee48
Revises: 
Create Date: 2025-08-11 13:11:55.240215

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '86904b35ee48'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'macro_indicators',
        sa.Column('indicator', sa.String(length=100), primary_key=True),
        sa.Column('value', sa.Numeric()),
        sa.Column('unit', sa.String(length=50)),
        sa.Column('description', sa.Text()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'macro_indicator_history',
        sa.Column('indicator', sa.String(length=100), sa.ForeignKey('macro_indicators.indicator'), primary_key=True),
        sa.Column('date', sa.Date(), primary_key=True),
        sa.Column('value', sa.Numeric()),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('macro_indicator_history')
    op.drop_table('macro_indicators')
