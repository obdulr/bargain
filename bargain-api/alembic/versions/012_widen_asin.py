"""Widen asin column to accommodate Impact.com deal IDs.

Revision ID: 012_widen_asin
Revises: 011_add_retailer_columns
Create Date: 2026-07-11
"""
from alembic import op
import sqlalchemy as sa

revision = "012_widen_asin"
down_revision = "011_add_retailer_columns"
branch_labels = None
depends_on = None


def upgrade():
    # Widen asin column from varchar(20) to varchar(100) to accommodate
    # Impact.com deal IDs like "impact_9383_6095491072282499229"
    op.alter_column("arbitrage_deals", "asin",
        existing_type=sa.String(20),
        type_=sa.String(100),
        existing_nullable=False,
    )


def downgrade():
    op.alter_column("arbitrage_deals", "asin",
        existing_type=sa.String(100),
        type_=sa.String(20),
        existing_nullable=False,
    )
