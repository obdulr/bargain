"""Add retailer and deal_source columns to arbitrage_deals

Revision ID: 011
Revises: 010_add_niche_system
Create Date: 2026-07-09
"""
from alembic import op
import sqlalchemy as sa


revision = "011_add_retailer_columns"
down_revision = "010_add_niche_system"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "arbitrage_deals",
        sa.Column("retailer", sa.String(100), server_default="amazon", nullable=True),
    )
    op.add_column(
        "arbitrage_deals",
        sa.Column("deal_source", sa.String(20), server_default="online", nullable=True),
    )
    op.create_index("ix_arbitrage_deals_retailer", "arbitrage_deals", ["retailer"])


def downgrade() -> None:
    op.drop_index("ix_arbitrage_deals_retailer", table_name="arbitrage_deals")
    op.drop_column("arbitrage_deals", "deal_source")
    op.drop_column("arbitrage_deals", "retailer")
