"""add default to access.id

Revision ID: 4c823c60d32f
Revises: 05cfd0319c1b
Create Date: 2025-07-01 22:13:07.846676

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers, used by Alembic.
revision = "4c823c60d32f"
down_revision = "05cfd0319c1b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade schema."""
    # Ensure the UUID generation extension is available
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')

    # Add server default for access.id so Postgres will auto-generate UUIDs
    op.alter_column(
        "access",
        "id",
        existing_type=postgresql.UUID(as_uuid=True),
        server_default=sa.text("gen_random_uuid()"),
        existing_nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove the server default on access.id
    op.alter_column(
        "access",
        "id",
        existing_type=postgresql.UUID(as_uuid=True),
        server_default=None,
        existing_nullable=False,
    )
