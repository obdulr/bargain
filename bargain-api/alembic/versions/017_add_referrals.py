"""Add referral fields and referral_claims table.

Revision ID: 017_add_referrals
Revises: 016_add_deal_score
Create Date: 2026-07-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "017_add_referrals"
down_revision = "016_add_deal_score"
branch_labels = None
depends_on = None


def upgrade():
    # Add referral fields to users
    op.add_column("users", sa.Column("referral_code", sa.String(20), nullable=True))
    op.add_column("users", sa.Column("referred_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True))
    op.add_column("users", sa.Column("referral_count", sa.Integer, server_default="0", nullable=False))

    # Unique index on referral_code and index on referred_by
    op.create_index("ix_users_referral_code", "users", ["referral_code"], unique=True)
    op.create_index("ix_users_referred_by", "users", ["referred_by"], unique=False)

    # Referral claims audit table
    op.create_table(
        "referral_claims",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("referrer_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("referee_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("referral_code", sa.String(20), nullable=False),
        sa.Column("points_awarded", sa.Integer, server_default="0", nullable=False),
        sa.Column("claimed_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )


def downgrade():
    op.drop_table("referral_claims")
    op.drop_index("ix_users_referred_by", table_name="users")
    op.drop_index("ix_users_referral_code", table_name="users")
    op.drop_column("users", "referral_count")
    op.drop_column("users", "referred_by")
    op.drop_column("users", "referral_code")
