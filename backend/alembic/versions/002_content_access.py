"""content access control

Revision ID: 002_content_access
Revises: 001_initial_schema
Create Date: 2026-04-15 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002_content_access"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE TYPE access_mode AS ENUM ('all_users', 'specific_users')")

    op.add_column(
        "contents",
        sa.Column(
            "access_mode",
            sa.Enum("all_users", "specific_users", name="access_mode", create_type=False),
            nullable=False,
            server_default="all_users",
        ),
    )

    op.create_table(
        "content_access",
        sa.Column("content_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "granted_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("granted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint("content_id", "user_id"),
        sa.ForeignKeyConstraint(["content_id"], ["contents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_content_access_content_id", "content_access", ["content_id"])
    op.create_index("ix_content_access_user_id", "content_access", ["user_id"])


def downgrade() -> None:
    op.drop_table("content_access")
    op.drop_column("contents", "access_mode")
    op.execute("DROP TYPE IF EXISTS access_mode")
