"""add webauthn passkey columns

Adds WebAuthn/passkey fields to the users table so users can authenticate
with passkeys in addition to (or instead of) passwords.

  - credential_id  (String)   base64url-encoded credential id
  - public_key     (LargeBinary) stored credential public key
  - sign_count     (Integer)  authenticator sign count (clone detection)
  - aaguid         (String)   authenticator model identifier

Revision ID: 007_add_webauthn_passkey_fields
Revises: 006_add_stripe_subscription_fields
Create Date: 2026-07-09
"""
from alembic import op
import sqlalchemy as sa


revision = "007_add_webauthn_passkey_fields"
down_revision = "006_add_stripe_subscription_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("credential_id", sa.String(255)))
    op.add_column("users", sa.Column("public_key", sa.LargeBinary()))
    op.add_column("users", sa.Column("sign_count", sa.Integer(), server_default="0"))
    op.add_column("users", sa.Column("aaguid", sa.String(255)))


def downgrade() -> None:
    op.drop_column("users", "aaguid")
    op.drop_column("users", "sign_count")
    op.drop_column("users", "public_key")
    op.drop_column("users", "credential_id")
