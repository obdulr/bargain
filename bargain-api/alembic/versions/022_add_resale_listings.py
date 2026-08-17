"""Add resale_listings table (resale pricing assistant).

Revision ID: 022_add_resale_listings
Revises: 021_add_watchlist_user_id_index
Create Date: 2026-08-16
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "022_add_resale_listings"
down_revision = "021_add_watchlist_user_id_index"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "resale_listings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("source_deal_id", UUID(as_uuid=True), sa.ForeignKey("arbitrage_deals.id"), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("search_query", sa.String(500)),
        sa.Column("sell_platform", sa.String(50), server_default="ebay"),
        sa.Column("buy_price", sa.Numeric(10, 2)),
        sa.Column("our_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("min_price", sa.Numeric(10, 2)),
        sa.Column("competitor_price", sa.Numeric(10, 2)),
        sa.Column("suggested_price", sa.Numeric(10, 2)),
        sa.Column("suggestion_reason", sa.String(255)),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("last_checked_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_resale_listings_user_id", "resale_listings", ["user_id"])


def downgrade():
    op.drop_index("ix_resale_listings_user_id", table_name="resale_listings")
    op.drop_table("resale_listings")
