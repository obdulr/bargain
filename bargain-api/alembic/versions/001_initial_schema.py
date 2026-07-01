"""initial schema

Revision ID: 001
Revises: 
Create Date: 2024-06-30 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(255)),
        sa.Column('subscription_tier', sa.String(50), default='free'),
        sa.Column('stripe_customer_id', sa.String(255)),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('NOW()'))
    )
    op.create_index('ix_users_email', 'users', ['email'])

    # Create subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('stripe_subscription_id', sa.String(255), unique=True),
        sa.Column('status', sa.String(50)),
        sa.Column('tier', sa.String(50)),
        sa.Column('current_period_end', sa.DateTime),
        sa.Column('cancel_at_period_end', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )

    # Create alerts table
    op.create_table(
        'alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.String),
        sa.Column('source_url', sa.String(500)),
        sa.Column('potential_profit', sa.Numeric(10, 2)),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('sent_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )

    # Create price_snapshots table
    op.create_table(
        'price_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('item_id', sa.String(255), nullable=False),
        sa.Column('retailer', sa.String(100), nullable=False),
        sa.Column('price', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(3), default='USD'),
        sa.Column('timestamp', sa.DateTime, server_default=sa.text('NOW()'))
    )
    op.create_index('ix_price_snapshots_item_id', 'price_snapshots', ['item_id'])
    op.create_index('ix_price_snapshots_timestamp', 'price_snapshots', ['timestamp'])

    # Create watchlist_items table
    op.create_table(
        'watchlist_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('item_name', sa.String(255), nullable=False),
        sa.Column('target_price', sa.Numeric(10, 2)),
        sa.Column('current_price', sa.Numeric(10, 2)),
        sa.Column('retailers', postgresql.JSON),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )


def downgrade() -> None:
    op.drop_table('watchlist_items')
    op.drop_table('price_snapshots')
    op.drop_table('alerts')
    op.drop_table('subscriptions')
    op.drop_table('users')
