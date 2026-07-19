"""Add PostgreSQL trigger to keep users.updated_at current on update.

Revision ID: 020_add_user_updated_at_trigger
Revises: 019_add_affiliate_clicks
Create Date: 2026-07-16
"""
from alembic import op

revision = "020_add_user_updated_at_trigger"
down_revision = "019_add_affiliate_clicks"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$ language 'plpgsql';
    """)

    op.execute("""
    DROP TRIGGER IF EXISTS update_users_updated_at ON users;
    CREATE TRIGGER update_users_updated_at
        BEFORE UPDATE ON users
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade():
    op.execute("DROP TRIGGER IF EXISTS update_users_updated_at ON users;")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")
