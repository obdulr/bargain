"""Add waitlist_entries table

Revision ID: 003
Revises: 002
Create Date: 2026-07-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'waitlist_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('plan', sa.String(255)),
        sa.Column('source', sa.String(255)),
        sa.Column('message', sa.String),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
    )
    op.create_index('ix_waitlist_entries_email', 'waitlist_entries', ['email'])


def downgrade() -> None:
    op.drop_table('waitlist_entries')
