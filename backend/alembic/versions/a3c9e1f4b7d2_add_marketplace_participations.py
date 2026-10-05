"""add marketplace participations

Revision ID: a3c9e1f4b7d2
Revises: 77e15e260710
Create Date: 2026-09-29 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3c9e1f4b7d2'
down_revision: Union[str, Sequence[str], None] = '77e15e260710'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'marketplace_participations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('region', sa.String(length=2), nullable=False),
        sa.Column('marketplace_id', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('country_code', sa.String(length=2), nullable=False),
        sa.Column('default_currency_code', sa.String(length=3), nullable=False),
        sa.Column('default_language_code', sa.String(length=10), nullable=False),
        sa.Column('domain_name', sa.String(length=100), nullable=False),
        sa.Column('store_name', sa.String(length=255), nullable=True),
        sa.Column('is_participating', sa.Boolean(), nullable=False),
        sa.Column('has_suspended_listings', sa.Boolean(), nullable=False),
        sa.Column('last_synced_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('region', 'marketplace_id', name='uq_marketplace_participations_region_marketplace'),
    )
    op.create_index(op.f('ix_marketplace_participations_region'), 'marketplace_participations', ['region'], unique=False)
    op.create_index(op.f('ix_marketplace_participations_marketplace_id'), 'marketplace_participations', ['marketplace_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_marketplace_participations_marketplace_id'), table_name='marketplace_participations')
    op.drop_index(op.f('ix_marketplace_participations_region'), table_name='marketplace_participations')
    op.drop_table('marketplace_participations')
