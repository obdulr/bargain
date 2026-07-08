"""Add niche system: niche column on arbitrage_deals + subscribed_niches on users

Revision ID: 010
Revises: 009_add_notification_logs
Create Date: 2026-07-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "010_add_niche_system"
down_revision = "009_add_notification_logs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Tag each arbitrage deal with its niche (electronics, tools_home_improvement, etc.)
    op.add_column(
        "arbitrage_deals",
        sa.Column("niche", sa.String(50), nullable=True),
    )
    op.create_index("ix_arbitrage_deals_niche", "arbitrage_deals", ["niche"])

    # User niche subscriptions — empty/NULL means "all niches"
    op.add_column(
        "users",
        sa.Column("subscribed_niches", postgresql.ARRAY(sa.String()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "subscribed_niches")
    op.drop_index("ix_arbitrage_deals_niche", table_name="arbitrage_deals")
    op.drop_column("arbitrage_deals", "niche")
