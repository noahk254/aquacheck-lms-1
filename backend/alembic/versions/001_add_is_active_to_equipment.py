"""add is_active to equipment

Revision ID: 001_add_is_active_to_equipment
Revises: 
Create Date: 2026-05-06
"""
from alembic import op
import sqlalchemy as sa

revision = "001_add_is_active_to_equipment"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("equipment", sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"))


def downgrade() -> None:
    op.drop_column("equipment", "is_active")
