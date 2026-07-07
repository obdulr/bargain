"""Add is_read and read_at columns to alerts table

Revision ID: 005_add_alert_read_status
Revises: 004_add_arbitrage
Create Date: 2026-07-08
"""
from alembic import op
import sqlalchemy as sa


revision = "005_add_alert_read_status"
down_revision = "004_add_arbitrage"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("alerts", sa.Column("is_read", sa.Boolean, server_default=sa.text("false"), nullable=False))
    op.add_column("alerts", sa.Column("read_at", sa.DateTime))


def downgrade() -> None:
    op.drop_column("alerts", "read_at")
    op.drop_column("alerts", "is_read")
