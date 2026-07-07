"""Add arbitrage deals and scan runs tables

Revision ID: 004
Revises: 003_add_waitlist
Create Date: 2026-07-07
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "004_add_arbitrage"
down_revision = "003_add_waitlist"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "arbitrage_deals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("asin", sa.String(20), nullable=False, index=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("image_url", sa.String(1000)),
        sa.Column("buy_url", sa.String(1000)),
        sa.Column("buy_platform", sa.String(50), server_default="amazon"),
        sa.Column("buy_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("sell_platform", sa.String(50), server_default="ebay"),
        sa.Column("sell_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("historical_avg", sa.Numeric(10, 2)),
        sa.Column("discrepancy", sa.Numeric(5, 4)),
        sa.Column("deal_tier", sa.String(20), server_default="arbitrage"),
        sa.Column("net_profit", sa.Numeric(10, 2)),
        sa.Column("roi", sa.Numeric(5, 4)),
        sa.Column("total_costs", sa.Numeric(10, 2)),
        sa.Column("platform_fee", sa.Numeric(10, 2)),
        sa.Column("bsr", sa.Integer),
        sa.Column("category", sa.String(100)),
        sa.Column("is_profitable", sa.Boolean, server_default=sa.text("false")),
        sa.Column("status", sa.String(50), server_default="active"),
        sa.Column("detected_at", sa.DateTime, server_default=sa.text("now()"), index=True),
        sa.Column("alerted_at", sa.DateTime),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()")),
    )

    op.create_table(
        "scan_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("scan_type", sa.String(50), server_default="amazon_ebay"),
        sa.Column("products_scanned", sa.Integer, server_default="0"),
        sa.Column("deals_found", sa.Integer, server_default="0"),
        sa.Column("deals_alerted", sa.Integer, server_default="0"),
        sa.Column("started_at", sa.DateTime, server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime),
        sa.Column("status", sa.String(50), server_default="running"),
        sa.Column("error", sa.String),
    )


def downgrade() -> None:
    op.drop_table("scan_runs")
    op.drop_table("arbitrage_deals")
