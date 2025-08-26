"""add research_notes

Revision ID: 4d358e082fd4
Revises: 3bba235f3ec0
Create Date: 2025-08-12 21:12:52.092592

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4d358e082fd4'
down_revision: Union[str, Sequence[str], None] = '3bba235f3ec0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'research_notes',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('summary', sa.Text()),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column(
            'last_updated',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('research_notes')
