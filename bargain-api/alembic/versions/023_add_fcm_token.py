"""Add fcm_token column to users table for Firebase Cloud Messaging

Revision ID: 023
Revises: 022
Create Date: 2026-08-28
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = "023"
down_revision = "022_add_resale_listings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("fcm_token", sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "fcm_token")
