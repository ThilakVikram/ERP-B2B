"""rename amazon_listings to amazon_items

Revision ID: 9e2a7c5d1f08
Revises: 2b65d4634610
Create Date: 2026-10-01 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '9e2a7c5d1f08'
down_revision: Union[str, Sequence[str], None] = '2b65d4634610'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INDEXES = [
    ('uq_amazon_listings_marketplace_sku', 'uq_amazon_items_marketplace_sku'),
    ('ix_amazon_listings_amazon_marketplace_id', 'ix_amazon_items_amazon_marketplace_id'),
    ('ix_amazon_listings_asin', 'ix_amazon_items_asin'),
    ('ix_amazon_listings_merchant_listing_id', 'ix_amazon_items_merchant_listing_id'),
]


def upgrade() -> None:
    """Upgrade schema."""
    op.rename_table('amazon_listings', 'amazon_items')
    for old, new in INDEXES:
        op.execute(f'ALTER TABLE amazon_items RENAME INDEX {old} TO {new}')


def downgrade() -> None:
    """Downgrade schema."""
    for old, new in INDEXES:
        op.execute(f'ALTER TABLE amazon_items RENAME INDEX {new} TO {old}')
    op.rename_table('amazon_items', 'amazon_listings')
