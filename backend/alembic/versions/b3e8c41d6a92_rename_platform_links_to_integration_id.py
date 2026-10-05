"""rename amazon_marketplaces / amazon_items links to integration_id

Revision ID: b3e8c41d6a92
Revises: a7d1fa5b2571
Create Date: 2026-10-01 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b3e8c41d6a92'
down_revision: Union[str, Sequence[str], None] = 'a7d1fa5b2571'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (table, old column, old index, new index); every column becomes integration_id.
RENAMES = [
    ('amazon_marketplaces', 'marketplace_participation_id',
     'ix_amazon_marketplaces_marketplace_participation_id', 'ix_amazon_marketplaces_integration_id'),
    ('amazon_items', 'merchant_listing_id',
     'ix_amazon_items_merchant_listing_id', 'ix_amazon_items_integration_id'),
]


def upgrade() -> None:
    """Upgrade schema."""
    # RENAME COLUMN keeps the data, type and foreign key.
    for table, column, old_index, new_index in RENAMES:
        op.execute(f'ALTER TABLE {table} RENAME COLUMN {column} TO integration_id, RENAME INDEX {old_index} TO {new_index}')


def downgrade() -> None:
    """Downgrade schema."""
    for table, column, old_index, new_index in RENAMES:
        op.execute(f'ALTER TABLE {table} RENAME COLUMN integration_id TO {column}, RENAME INDEX {new_index} TO {old_index}')
