"""Add score column to arbitrage_deals table.

Revision ID: 016_add_deal_score
Revises: 015_add_seller_voucher
Create Date: 2026-07-16
"""
from alembic import op
import sqlalchemy as sa


revision = "016_add_deal_score"
down_revision = "015_add_seller_voucher"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "arbitrage_deals",
        sa.Column("score", sa.Numeric(10, 4), server_default="0", nullable=False),
    )


def downgrade():
    op.drop_column("arbitrage_deals", "score")
