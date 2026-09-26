"""add default to access.id

Revision ID: 586a555f3122
Revises: 4c823c60d32f
Create Date: 2025-07-01 22:XX:XX.XXXXXX

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "586a555f3122"
down_revision = "4c823c60d32f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) ensure the pgcrypto extension is available
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')

    # 2) add the server-side default so Postgres will auto-generate UUIDs
    op.alter_column(
        "access",
        "id",
        existing_type=postgresql.UUID(as_uuid=True),
        server_default=sa.text("gen_random_uuid()"),
        existing_nullable=False,
    )


def downgrade() -> None:
    # remove the default
    op.alter_column(
        "access",
        "id",
        existing_type=postgresql.UUID(as_uuid=True),
        server_default=None,
        existing_nullable=False,
    )
    # (optional) drop the extension if you really want to roll it back
    # op.execute('DROP EXTENSION IF EXISTS "pgcrypto";')
