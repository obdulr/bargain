"""Add newsletter_subscribers table for email deal digest

Revision ID: 024
Revises: 023
Create Date: 2026-09-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers
revision = "024"
down_revision = "023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "newsletter_subscribers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("subscribed_at", sa.DateTime, nullable=True),
        sa.Column("unsubscribed_at", sa.DateTime, nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=True),
        sa.Column("source", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("newsletter_subscribers")
