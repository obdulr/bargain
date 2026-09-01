"""Add submitted_by/submitted_at to coupon_codes and merge 024 branches.

Revision ID: 025
Revises: ('024', '024_add_affiliate_click_columns')
Create Date: 2026-09-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = "025"
down_revision = ("024", "024_add_affiliate_click_columns")
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("coupon_codes", sa.Column("submitted_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True))
    op.add_column("coupon_codes", sa.Column("submitted_at", sa.DateTime, nullable=True))
    op.create_index("ix_coupon_codes_submitted_by", "coupon_codes", ["submitted_by"])


def downgrade() -> None:
    op.drop_index("ix_coupon_codes_submitted_by", table_name="coupon_codes")
    op.drop_column("coupon_codes", "submitted_at")
    op.drop_column("coupon_codes", "submitted_by")
