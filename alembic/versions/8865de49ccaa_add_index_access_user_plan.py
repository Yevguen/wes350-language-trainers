"""add index on access(user_id, plan) (idempotent)"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "8865de49ccaa"  # ← real ID, matches the filename
down_revision = "ba0e4627399e"  # ← your repair migration
branch_labels = None
depends_on = None


def upgrade():
    # Use raw SQL so it won't fail if the index already exists (you created it manually).
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_access_user_plan ON access (user_id, plan)"
    )


def downgrade():
    # Idempotent drop as well.
    op.execute("DROP INDEX IF EXISTS ix_access_user_plan")
