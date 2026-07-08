"""Add notification logs table

Revision ID: 009
Revises: 008_add_coupon_codes
Create Date: 2026-07-07
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "009_add_notification_logs"
down_revision = "008_add_coupon_codes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notification_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("deal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("arbitrage_deals.id"), nullable=True),
        sa.Column("asin", sa.String(20), index=True),
        sa.Column("channel", sa.String(50), nullable=False),
        sa.Column("recipient", sa.String(255)),
        sa.Column("message", sa.String),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("error", sa.String),
        sa.Column("sent_at", sa.DateTime),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("notification_logs")
