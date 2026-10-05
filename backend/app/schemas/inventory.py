from datetime import datetime

from app.integration.amazon.marketplaces import Region
from app.schemas.base import CamelModel


class ResearchingQuantityEntryOut(CamelModel):
    name: str | None = None
    quantity: int | None = None


class FbaInventorySummaryOut(CamelModel):
    id: int
    region: Region
    marketplace_id: str
    seller_sku: str
    asin: str | None
    fn_sku: str | None
    condition: str | None
    product_name: str | None
    total_quantity: int
    stores: list[str] | None
    last_updated_time: datetime | None
    fulfillable_quantity: int
    inbound_working_quantity: int
    inbound_shipped_quantity: int
    inbound_receiving_quantity: int
    total_reserved_quantity: int
    pending_customer_order_quantity: int
    pending_transshipment_quantity: int
    fc_processing_quantity: int
    total_researching_quantity: int
    researching_quantity_breakdown: list[ResearchingQuantityEntryOut] | None
    total_unfulfillable_quantity: int
    customer_damaged_quantity: int
    warehouse_damaged_quantity: int
    distributor_damaged_quantity: int
    carrier_damaged_quantity: int
    defective_quantity: int
    expired_quantity: int
    last_synced_at: datetime
    updated_at: datetime


class FbaInventorySyncOut(CamelModel):
    region: Region
    marketplace_id: str
    count: int
    synced_at: datetime
