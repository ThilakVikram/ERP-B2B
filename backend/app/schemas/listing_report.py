from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.integration.amazon.marketplaces import Region
from app.schemas.base import CamelModel


class ListingReportCreateIn(CamelModel):
    """Marketplaces to take a listings snapshot of; one report each."""

    marketplace_ids: list[str] = Field(min_length=1, max_length=25)


class ListingsSummaryOut(CamelModel):
    """Stored listings for one marketplace."""

    region: Region
    marketplace_id: str
    listing_count: int
    active_count: int
    total_quantity: int
    last_updated_at: datetime | None


class MerchantListingOut(CamelModel):
    id: int
    amazon_report_id: int
    region: Region
    marketplace_id: str
    seller_sku: str
    listing_id: str | None
    item_name: str | None
    asin: str | None
    product_id: str | None
    product_id_type: str | None
    price: Decimal | None
    quantity: int | None
    pending_quantity: int | None
    open_date: str | None
    item_condition: str | None
    fulfillment_channel: str | None
    status: str | None
    created_at: datetime
    updated_at: datetime
