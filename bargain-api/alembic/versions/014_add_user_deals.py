"""Add user_submitted_deals, deal_votes tables and aura fields on users.

Revision ID: 014_add_user_deals
Revises: 013_add_phone_number
Create Date: 2026-07-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "014_add_user_deals"
down_revision = "013_add_phone_number"
branch_labels = None
depends_on = None


def upgrade():
    # Add aura fields to users
    op.add_column("users", sa.Column("aura_points", sa.Integer, server_default="0", nullable=False))
    op.add_column("users", sa.Column("aura_tier", sa.String(20), server_default="hunter", nullable=False))

    # User-submitted deals
    op.create_table(
        "user_submitted_deals",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("url", sa.String(1000), nullable=False),
        sa.Column("image_url", sa.String(1000)),
        sa.Column("retailer", sa.String(100), nullable=False),
        sa.Column("original_price", sa.Numeric(10, 2)),
        sa.Column("sale_price", sa.Numeric(10, 2)),
        sa.Column("discount_percent", sa.Float),
        sa.Column("category", sa.String(100)),
        sa.Column("description", sa.Text),
        sa.Column("status", sa.String(20), server_default="pending", nullable=False, index=True),
        sa.Column("rejection_reason", sa.String(500)),
        sa.Column("reviewed_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime),
        sa.Column("upvotes", sa.Integer, server_default="0", nullable=False),
        sa.Column("downvotes", sa.Integer, server_default="0", nullable=False),
        sa.Column("score", sa.Integer, server_default="0", nullable=False),
        sa.Column("promoted_deal_id", UUID(as_uuid=True), sa.ForeignKey("arbitrage_deals.id"), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False, index=True),
    )

    # Deal votes
    op.create_table(
        "deal_votes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("deal_id", UUID(as_uuid=True), sa.ForeignKey("user_submitted_deals.id"), nullable=False, index=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("vote", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("deal_id", "user_id", name="uq_deal_vote_user"),
    )


def downgrade():
    op.drop_table("deal_votes")
    op.drop_table("user_submitted_deals")
    op.drop_column("users", "aura_tier")
    op.drop_column("users", "aura_points")
