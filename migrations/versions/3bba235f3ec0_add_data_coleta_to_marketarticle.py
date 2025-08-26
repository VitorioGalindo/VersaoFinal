"""add data_coleta to MarketArticle

Revision ID: 3bba235f3ec0
Revises: 5a6c7d8e9f10
Create Date: 2025-08-12 17:09:26.806461

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3bba235f3ec0'
down_revision: Union[str, Sequence[str], None] = '5a6c7d8e9f10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'artigos_mercado' not in inspector.get_table_names():
        return
    op.add_column('artigos_mercado', sa.Column('data_coleta', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'artigos_mercado' not in inspector.get_table_names():
        return
    op.drop_column('artigos_mercado', 'data_coleta')
