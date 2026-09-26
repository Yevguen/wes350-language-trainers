"""add access table

Revision ID: 05cfd0319c1b
Revises: 7a6054662e36
Create Date: 2025-06-28 11:07:52.073406

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers, used by Alembic.
revision: str = "05cfd0319c1b"
down_revision: Union[str, None] = "7a6054662e36"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "access",
        sa.Column(
            "id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False
        ),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("plan", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
    )


def downgrade() -> None:
    op.drop_table("access")
