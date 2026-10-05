from datetime import datetime
from decimal import Decimal

from app.integration.amazon.marketplaces import Region
from app.schemas.base import CamelModel
from app.schemas.sync_mode import SyncMode


class AmazonItemMarketplaceOut(CamelModel):
    """The marketplace an item belongs to, embedded in the item."""

    id: int
    region: Region
    marketplace_id: str
    name: str
    country_code: str


class AmazonItemOut(CamelModel):
    id: int
    amazon_marketplace_id: int
    integration_id: int | None
    marketplace: AmazonItemMarketplaceOut
    seller_sku: str
    asin: str | None
    fn_sku: str | None
    title: str | None
    item_condition: str | None
    fulfillment_channel: str | None
    price: Decimal | None
    currency_code: str | None
    image_url: str | None
    status: str | None
    created_at: datetime
    updated_at: datetime


class AmazonItemPageOut(CamelModel):
    total: int
    items: list[AmazonItemOut]


class AmazonItemSyncOut(CamelModel):
    """Result of creating/updating items from the integration's merchant listings.

    skipped: listings whose marketplace has no amazon_marketplaces row yet (sync marketplaces first).
    """

    mode: SyncMode
    created: int
    updated: int
    skipped: int
