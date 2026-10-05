from datetime import date, datetime, timezone
from decimal import Decimal

from pydantic import model_validator

from app.config import REPORT_MAX_RANGE_DAYS
from app.integration.amazon.marketplaces import Region
from app.schemas.base import CamelModel



class OrderReportCreateIn(CamelModel):
    """Period (whole days, UTC) of orders to include, by purchase date."""

    marketplace_id: str
    start_date: date
    end_date: date  # inclusive

    @model_validator(mode="after")
    def _check_date_range(self) -> "OrderReportCreateIn":
        if self.end_date < self.start_date:
            raise ValueError("endDate must be on or after startDate")
        if self.end_date > datetime.now(timezone.utc).date():
            raise ValueError("endDate cannot be in the future")
        days = (self.end_date - self.start_date).days + 1
        if days > REPORT_MAX_RANGE_DAYS:
            raise ValueError(f"Date range cannot exceed {REPORT_MAX_RANGE_DAYS} days (got {days})")
        return self


class OrderReportItemOut(CamelModel):
    id: int
    amazon_report_id: int
    region: Region
    marketplace_id: str
    amazon_order_id: str
    order_item_id: str
    merchant_order_id: str | None
    purchase_date: datetime | None
    last_updated_date: datetime | None
    order_status: str | None
    fulfillment_channel: str | None
    sales_channel: str | None
    ship_service_level: str | None
    product_name: str | None
    sku: str
    asin: str | None
    item_status: str | None
    quantity: int | None
    currency: str | None
    item_price: Decimal | None
    item_tax: Decimal | None
    shipping_price: Decimal | None
    shipping_tax: Decimal | None
    gift_wrap_price: Decimal | None
    gift_wrap_tax: Decimal | None
    item_promotion_discount: Decimal | None
    ship_promotion_discount: Decimal | None
    ship_city: str | None
    ship_state: str | None
    ship_postal_code: str | None
    ship_country: str | None
    promotion_ids: str | None
    is_business_order: bool | None
    raw: dict
    created_at: datetime


class OrderItemsSummaryOut(CamelModel):
    """Stored order items for one marketplace."""

    region: Region
    marketplace_id: str
    row_count: int
    order_count: int
    first_purchase_date: datetime | None
    last_purchase_date: datetime | None
    last_stored_at: datetime | None

