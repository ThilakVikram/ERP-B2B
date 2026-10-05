from datetime import datetime

from app.integration.amazon.marketplaces import Region
from app.schemas.base import CamelModel
from app.schemas.sync_mode import SyncMode


class AmazonMarketplaceOut(CamelModel):
    id: int
    integration_id: int | None
    region: Region
    marketplace_id: str
    name: str
    country_code: str
    currency_code: str
    language_code: str
    domain_name: str
    store_name: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AmazonMarketplaceSyncOut(CamelModel):
    """Result of creating/updating marketplaces from the integration's marketplace participations."""

    mode: SyncMode
    created: int
    updated: int
    marketplaces: list[AmazonMarketplaceOut]
