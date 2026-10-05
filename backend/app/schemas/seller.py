from datetime import datetime

from app.integration.amazon.marketplaces import Region
from app.schemas.base import CamelModel


class MarketplaceParticipationOut(CamelModel):
    id: int
    region: Region
    marketplace_id: str
    name: str
    country_code: str
    default_currency_code: str
    default_language_code: str
    domain_name: str
    store_name: str | None
    is_participating: bool
    has_suspended_listings: bool
    last_synced_at: datetime
    updated_at: datetime


class MarketplaceParticipationSyncOut(CamelModel):
    region: Region
    count: int
    participations: list[MarketplaceParticipationOut]
