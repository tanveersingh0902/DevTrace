"""Add registration, safe audit events, and shared authentication rate limits.

Revision ID: 20261117_0002
Revises: 20261108_0001
"""

from alembic import op
import sqlalchemy as sa

revision = "20261117_0002"
down_revision = "20261108_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.CheckConstraint("email = lower(btrim(email))", name="ck_users_email_normalized"),
        sa.CheckConstraint("length(btrim(display_name)) > 0", name="ck_users_display_name"),
    )
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("target_type", sa.String(32), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column("request_id", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_events_actor_created", "audit_events", ["actor_id", "created_at"])
    op.create_index("ix_audit_events_request_id", "audit_events", ["request_id"])
    op.create_table(
        "auth_rate_limits",
        sa.Column("scope", sa.String(32), nullable=False),
        sa.Column("key_hash", sa.String(64), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("scope", "key_hash"),
        sa.CheckConstraint("attempts > 0", name="ck_auth_rate_limits_attempts"),
    )
    op.create_index("ix_auth_rate_limits_expires_at", "auth_rate_limits", ["expires_at"])


def downgrade() -> None:
    op.drop_table("auth_rate_limits")
    op.drop_table("audit_events")
    op.drop_table("users")
