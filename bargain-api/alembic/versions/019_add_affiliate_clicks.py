"""Add affiliate_clicks table.

Revision ID: 019_add_affiliate_clicks
Revises: 018_add_notification_preferences
Create Date: 2026-07-16
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "019_add_affiliate_clicks"
down_revision = "018_add_notification_preferences"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "affiliate_clicks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("deal_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("retailer", sa.String(50)),
        sa.Column("original_url", sa.Text),
        sa.Column("affiliate_url", sa.Text),
        sa.Column("asin", sa.String(20), nullable=True),
        sa.Column("clicked_at", sa.DateTime, server_default=sa.text("NOW()"), nullable=False),
        sa.Column("converted", sa.Boolean, server_default=sa.text("false"), nullable=False),
        sa.Column("commission_earned", sa.Float, server_default=sa.text("0.0"), nullable=False),
        sa.ForeignKeyConstraint(["deal_id"], ["arbitrage_deals.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index("ix_affiliate_clicks_asin", "affiliate_clicks", ["asin"])
    op.create_index("ix_affiliate_clicks_clicked_at", "affiliate_clicks", ["clicked_at"])


def downgrade():
    op.drop_index("ix_affiliate_clicks_clicked_at", table_name="affiliate_clicks")
    op.drop_index("ix_affiliate_clicks_asin", table_name="affiliate_clicks")
    op.drop_table("affiliate_clicks")
