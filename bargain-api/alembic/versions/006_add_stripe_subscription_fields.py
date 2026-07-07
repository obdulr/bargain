"""add stripe subscription fields

Adds stripe_subscription_id to the users table to track the user's active
Stripe subscription alongside the existing stripe_customer_id.

Revision ID: 006_add_stripe_subscription_fields
Revises: 005_add_alert_read_status
Create Date: 2026-07-09
"""
from alembic import op
import sqlalchemy as sa


revision = "006_add_stripe_subscription_fields"
down_revision = "005_add_alert_read_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("stripe_subscription_id", sa.String(255)))


def downgrade() -> None:
    op.drop_column("users", "stripe_subscription_id")
