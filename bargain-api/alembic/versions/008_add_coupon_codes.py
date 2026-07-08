"""Add coupon codes table

Revision ID: 008
Revises: 007_add_webauthn_passkey_fields
Create Date: 2026-07-07
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "008_add_coupon_codes"
down_revision = "007_add_webauthn_passkey_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "coupon_codes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("code", sa.String(100), nullable=False, index=True),
        sa.Column("retailer", sa.String(100), nullable=False, index=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.String),
        sa.Column("discount_type", sa.String(20), server_default="percentage"),
        sa.Column("discount_value", sa.Numeric(10, 2), server_default="0"),
        sa.Column("min_purchase", sa.Numeric(10, 2)),
        sa.Column("max_discount", sa.Numeric(10, 2)),
        sa.Column("category", sa.String(100)),
        sa.Column("product_url", sa.String(1000)),
        sa.Column("source", sa.String(100), server_default="scraped"),
        sa.Column("source_url", sa.String(1000)),
        sa.Column("expires_at", sa.DateTime, index=True),
        sa.Column("verified", sa.Boolean, server_default=sa.text("false")),
        sa.Column("verified_at", sa.DateTime),
        sa.Column("times_used", sa.Integer, server_default="0"),
        sa.Column("success_count", sa.Integer, server_default="0"),
        sa.Column("fail_count", sa.Integer, server_default="0"),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("scraped_at", sa.DateTime, server_default=sa.text("now()")),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("coupon_codes")
