"""Add user_agent, referrer, ip_hash columns to affiliate_clicks.

The affiliate_clicks table was created in 019_add_affiliate_clicks but
lacked the columns needed for richer click analytics (browser/user-agent,
referring page, and a privacy-preserving IP hash). This migration adds
those columns so the redirect-based click tracker can record them.

Revision ID: 024_add_affiliate_click_columns
Revises: 023_add_fcm_token
Create Date: 2026-07-17
"""
from alembic import op
import sqlalchemy as sa

revision = "024_add_affiliate_click_columns"
down_revision = "023"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("affiliate_clicks", sa.Column("user_agent", sa.Text, nullable=True))
    op.add_column("affiliate_clicks", sa.Column("referrer", sa.Text, nullable=True))
    op.add_column("affiliate_clicks", sa.Column("ip_hash", sa.String(64), nullable=True))
    op.create_index("ix_affiliate_clicks_retailer", "affiliate_clicks", ["retailer"])
    op.create_index("ix_affiliate_clicks_deal_id", "affiliate_clicks", ["deal_id"])


def downgrade():
    op.drop_index("ix_affiliate_clicks_deal_id", table_name="affiliate_clicks")
    op.drop_index("ix_affiliate_clicks_retailer", table_name="affiliate_clicks")
    op.drop_column("affiliate_clicks", "ip_hash")
    op.drop_column("affiliate_clicks", "referrer")
    op.drop_column("affiliate_clicks", "user_agent")
