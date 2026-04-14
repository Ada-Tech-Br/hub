"""initial schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("type", sa.Enum("internal", "external", name="user_type", create_type=False), nullable=False, server_default="external"),
        sa.Column("role", sa.Enum("admin", "user", name="user_role", create_type=False), nullable=False, server_default="user"),
        sa.Column("auth_provider", sa.Enum("google", "otp", name="auth_provider", create_type=False), nullable=False, server_default="otp"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("otp_secret", sa.String(64), nullable=True),
        sa.Column("otp_expires_at", sa.String(64), nullable=True),
        sa.Column("google_id", sa.String(255), nullable=True),
        sa.Column("avatar_url", sa.String(512), nullable=True),
        # Audit
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_id", "users", ["id"])

    # Contents table
    op.create_table(
        "contents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("type", sa.Enum("project", "file", name="content_type", create_type=False), nullable=False),
        sa.Column("icon", sa.String(128), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("external_url", sa.String(2048), nullable=True),
        sa.Column("file_type", sa.Enum("html", "zip", "external", name="file_type", create_type=False), nullable=True),
        sa.Column("s3_path", sa.String(1024), nullable=True),
        sa.Column("uploaded_file_path", sa.String(1024), nullable=True),
        # Audit
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_contents_title", "contents", ["title"])
    op.create_index("ix_contents_id", "contents", ["id"])


def downgrade() -> None:
    op.drop_table("contents")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS file_type")
    op.execute("DROP TYPE IF EXISTS content_type")
    op.execute("DROP TYPE IF EXISTS auth_provider")
    op.execute("DROP TYPE IF EXISTS user_role")
    op.execute("DROP TYPE IF EXISTS user_type")
