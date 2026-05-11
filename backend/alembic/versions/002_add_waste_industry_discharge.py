"""add waste_industry_type and discharge_destination to samples

Revision ID: 002_add_waste_industry_discharge
Revises: 001_add_is_active_to_equipment
Create Date: 2026-05-11
"""
from alembic import op
import sqlalchemy as sa

revision = "002_add_waste_industry_discharge"
down_revision = "001_add_is_active_to_equipment"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("samples", sa.Column("waste_industry_type", sa.String(), nullable=True))
    op.add_column("samples", sa.Column("discharge_destination", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("samples", "discharge_destination")
    op.drop_column("samples", "waste_industry_type")
