"""Establish Phase 1 Alembic history.

Revision ID: 20261108_0001
Revises:
Create Date: 2026-11-08
"""

revision = "20261108_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """No domain schema exists during the foundation phase."""


def downgrade() -> None:
    """No domain schema exists during the foundation phase."""
