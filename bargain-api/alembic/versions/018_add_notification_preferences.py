"""Add notification preference columns to users.

Revision ID: 018_add_notification_preferences
Revises: 017_add_referrals
Create Date: 2026-07-22
"""
from alembic import op
import sqlalchemy as sa

revision = "018_add_notification_preferences"
down_revision = "017_add_referrals"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("email_deal_alerts", sa.Boolean, server_default="true", nullable=False))
    op.add_column("users", sa.Column("sms_deal_alerts", sa.Boolean, server_default="false", nullable=False))
    op.add_column("users", sa.Column("discord_alerts", sa.Boolean, server_default="false", nullable=False))
    op.add_column("users", sa.Column("telegram_alerts", sa.Boolean, server_default="false", nullable=False))
    op.add_column("users", sa.Column("push_notifications", sa.Boolean, server_default="false", nullable=False))
    op.add_column("users", sa.Column("weekly_digest", sa.Boolean, server_default="true", nullable=False))
    op.add_column("users", sa.Column("glitch_alerts", sa.Boolean, server_default="true", nullable=False))


def downgrade():
    op.drop_column("users", "glitch_alerts")
    op.drop_column("users", "weekly_digest")
    op.drop_column("users", "push_notifications")
    op.drop_column("users", "telegram_alerts")
    op.drop_column("users", "discord_alerts")
    op.drop_column("users", "sms_deal_alerts")
    op.drop_column("users", "email_deal_alerts")
