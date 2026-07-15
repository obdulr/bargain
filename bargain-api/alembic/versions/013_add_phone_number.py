"""Add phone_number column to users table for SMS alerts.

Revision ID: 013_add_phone_number
Revises: 012_widen_asin
Create Date: 2026-07-15
"""
from alembic import op
import sqlalchemy as sa

revision = "013_add_phone_number"
down_revision = "012_widen_asin"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("phone_number", sa.String(20), nullable=True))


def downgrade():
    op.drop_column("users", "phone_number")
