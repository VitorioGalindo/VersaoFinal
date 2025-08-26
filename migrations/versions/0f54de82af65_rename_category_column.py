"""rename category column

Revision ID: 0f54de82af65
Revises: 86904b35ee48
Create Date: 2025-08-11 15:05:18.107629

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0f54de82af65'
down_revision: Union[str, Sequence[str], None] = '86904b35ee48'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema by renaming or adding column."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    try:
        columns = [c["name"] for c in inspector.get_columns("cvm_documents")]
    except sa.exc.NoSuchTableError:
        return
    if "category" in columns:
        op.alter_column(
            "cvm_documents", "category", new_column_name="document_category"
        )
    elif "document_category" not in columns:
        op.add_column(
            "cvm_documents",
            sa.Column("document_category", sa.String(), nullable=True),
        )


def downgrade() -> None:
    """Revert schema changes."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    try:
        columns = [c["name"] for c in inspector.get_columns("cvm_documents")]
    except sa.exc.NoSuchTableError:
        return
    if "document_category" in columns and "category" not in columns:
        op.alter_column(
            "cvm_documents", "document_category", new_column_name="category"
        )
    elif "document_category" in columns:
        op.drop_column("cvm_documents", "document_category")
