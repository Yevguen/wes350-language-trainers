"""repair_access_uuid_id_tz_expires_fk

Revision ID: ba0e4627399e
Revises: 586a555f3122
Create Date: 2025-09-01 12:28:48.533035

This migration repairs the `access` table to:
- use UUID primary key with default gen_random_uuid(),
- ensure `user_id` is UUID with ON DELETE CASCADE FK to user(id),
- convert `expires_at` to timestamptz (timezone-aware),
and is safe to run repeatedly (idempotent).
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# ---- revision identifiers ----
revision = "ba0e4627399e"
down_revision = "586a555f3122"
branch_labels = None
depends_on = None


def _scalar(conn, sql, **params):
    return conn.execute(sa.text(sql), params).scalar()


def upgrade():
    conn = op.get_bind()

    # 0) Ensure the UUID generator is available
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')

    # ---- Detect current column types ----
    id_type = _scalar(
        conn,
        """
        SELECT data_type
        FROM information_schema.columns
        WHERE table_name = 'access' AND column_name = 'id'
        """,
    )
    user_id_type = _scalar(
        conn,
        """
        SELECT data_type
        FROM information_schema.columns
        WHERE table_name = 'access' AND column_name = 'user_id'
        """,
    )
    expires_type = _scalar(
        conn,
        """
        SELECT data_type
        FROM information_schema.columns
        WHERE table_name = 'access' AND column_name = 'expires_at'
        """,
    )

    # ---- 1) Primary key: make it UUID with default gen_random_uuid() ----
    if id_type != "uuid":
        op.add_column(
            "access",
            sa.Column(
                "id_new",
                postgresql.UUID(as_uuid=True),
                server_default=sa.text("gen_random_uuid()"),
                nullable=False,
            ),
        )
        pk_name = (
            _scalar(
                conn,
                """
            SELECT tc.constraint_name
            FROM information_schema.table_constraints tc
            WHERE tc.table_name = 'access' AND tc.constraint_type = 'PRIMARY KEY'
            """,
            )
            or "access_pkey"
        )
        op.drop_constraint(pk_name, "access", type_="primary")
        op.drop_column("access", "id")
        op.alter_column("access", "id_new", new_column_name="id")
        op.create_primary_key("access_pkey", "access", ["id"])
    else:
        # Ensure default exists on existing UUID PK
        op.alter_column(
            "access",
            "id",
            existing_type=postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            existing_nullable=False,
        )

    # ---- 2) Foreign key: user_id must be UUID and ON DELETE CASCADE ----
    fk_name = _scalar(
        conn,
        """
        SELECT tc.constraint_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name
         AND tc.table_schema = kcu.table_schema
        WHERE tc.table_name = 'access'
          AND tc.constraint_type = 'FOREIGN KEY'
          AND kcu.column_name = 'user_id'
        """,
    )
    if fk_name:
        op.drop_constraint(fk_name, "access", type_="foreignkey")

    if user_id_type != "uuid":
        op.alter_column(
            "access",
            "user_id",
            type_=postgresql.UUID(as_uuid=True),
            postgresql_using="user_id::uuid",
            existing_nullable=False,
        )

    op.create_foreign_key(
        "access_user_id_fkey",
        source_table="access",
        referent_table="user",  # Alembic will quote reserved name as needed
        local_cols=["user_id"],
        remote_cols=["id"],
        ondelete="CASCADE",
    )

    # ---- 3) expires_at: make it timestamptz (tz-aware) ----
    if expires_type == "timestamp without time zone":
        op.alter_column(
            "access",
            "expires_at",
            type_=sa.DateTime(timezone=True),
            existing_type=sa.DateTime(timezone=False),
            postgresql_using="expires_at AT TIME ZONE 'UTC'",
            existing_nullable=True,
        )

    # ---- 4) Optional index to speed lookups by (user_id, plan) ----
    # op.create_index("ix_access_user_plan", "access", ["user_id", "plan"], unique=False)


def downgrade():
    # Complex and lossy to revert; intentionally unsupported.
    raise RuntimeError("Downgrade not supported for this repair migration")
