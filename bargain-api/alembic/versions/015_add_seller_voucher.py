"""Add seller fields, voucher_winners, seller_submissions tables.

Revision ID: 015_add_seller_voucher
Revises: 014_add_user_deals
Create Date: 2026-07-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "015_add_seller_voucher"
down_revision = "014_add_user_deals"
branch_labels = None
depends_on = None


def upgrade():
    # Seller + login streak fields on users
    op.add_column("users", sa.Column("last_login_at", sa.DateTime, nullable=True))
    op.add_column("users", sa.Column("login_streak", sa.Integer, server_default="0", nullable=False))
    op.add_column("users", sa.Column("is_verified_seller", sa.Boolean, server_default="false", nullable=False))
    op.add_column("users", sa.Column("seller_store_name", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("seller_website", sa.String(1000), nullable=True))

    # Voucher winners
    op.create_table(
        "voucher_winners",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("month", sa.String(7), nullable=False, index=True),
        sa.Column("prize_amount", sa.Numeric(10, 2), server_default="100", nullable=False),
        sa.Column("aura_points_at_draw", sa.Integer),
        sa.Column("drawn_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("paid_at", sa.DateTime),
        sa.Column("status", sa.String(20), server_default="pending", nullable=False),
    )

    # Seller submissions
    op.create_table(
        "seller_submissions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("seller_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("submission_type", sa.String(20), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("url", sa.String(1000), nullable=False),
        sa.Column("retailer", sa.String(100), nullable=False),
        sa.Column("image_url", sa.String(1000)),
        sa.Column("category", sa.String(100)),
        sa.Column("description", sa.Text),
        sa.Column("coupon_code", sa.String(100)),
        sa.Column("discount_type", sa.String(20)),
        sa.Column("discount_value", sa.Numeric(10, 2)),
        sa.Column("expires_at", sa.DateTime),
        sa.Column("original_price", sa.Numeric(10, 2)),
        sa.Column("sale_price", sa.Numeric(10, 2)),
        sa.Column("status", sa.String(20), server_default="pending", nullable=False, index=True),
        sa.Column("reviewed_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime),
        sa.Column("promoted_deal_id", UUID(as_uuid=True), sa.ForeignKey("arbitrage_deals.id"), nullable=True),
        sa.Column("promoted_coupon_id", UUID(as_uuid=True), sa.ForeignKey("coupon_codes.id"), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False, index=True),
    )


def downgrade():
    op.drop_table("seller_submissions")
    op.drop_table("voucher_winners")
    op.drop_column("users", "seller_website")
    op.drop_column("users", "seller_store_name")
    op.drop_column("users", "is_verified_seller")
    op.drop_column("users", "login_streak")
    op.drop_column("users", "last_login_at")
