"""Add index on watchlist_items.user_id.

Revision ID: 021_add_watchlist_user_id_index
Revises: 020_add_user_updated_at_trigger
Create Date: 2026-07-16
"""
from alembic import op

revision = "021_add_watchlist_user_id_index"
down_revision = "020_add_user_updated_at_trigger"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("ix_watchlist_items_user_id", "watchlist_items", ["user_id"])


def downgrade():
    op.drop_index("ix_watchlist_items_user_id", table_name="watchlist_items")
