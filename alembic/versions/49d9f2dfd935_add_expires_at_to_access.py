"""add expires_at to access

Revision ID: 49d9f2dfd935
Revises: 8865de49ccaa
Create Date: 2025-09-02 13:19:23.668640
"""

from alembic import op
import sqlalchemy as sa

# Alembic identifiers
revision = "49d9f2dfd935"  # ← must match the real revision id
down_revision = "8865de49ccaa"
branch_labels = None
depends_on = None


def upgrade():
    # Add the column
    op.add_column(
        "access",
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Helpful index for checks
    op.create_index(
        "ix_access_user_plan_expires",
        "access",
        ["user_id", "plan", "expires_at"],
        unique=False,
    )

    # Optional: backfill so existing grants start working immediately
    op.execute(
        "UPDATE access "
        "SET expires_at = now() + interval '120 hours' "
        "WHERE expires_at IS NULL;"
    )


def downgrade():
    op.drop_index("ix_access_user_plan_expires", table_name="access")
    op.drop_column("access", "expires_at")
