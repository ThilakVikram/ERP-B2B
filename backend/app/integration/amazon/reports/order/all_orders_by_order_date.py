"""GET_FLAT_FILE_ALL_ORDERS_DATA_BY_ORDER_DATE_GENERAL

Tab-delimited flat file with one row per order item, for all orders *placed* between
dataStartTime and dataEndTime (all statuses, MFN and FBA). Amazon allows at most 30 days per request.
Docs: https://developer-docs.amazon.com/sp-api/docs/report-type-values-order

    report = AllOrdersByOrderDateReport(AmazonCredentials.for_marketplace(Marketplace.IN))
    report_id = report.request(start, end)                   # returns immediately
    rows = report.download_rows(report.wait(report_id))      # blocking: run in a background task
"""

import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from spapi.models.reports_v2021_06_30 import Report

from app.integration.amazon.config import AmazonCredentials
from app.integration.amazon.reports.fields import (
    normalize_row,
    to_bool,
    to_datetime,
    to_decimal,
    to_int,
    to_str,
)
from app.integration.amazon.reports.order.report_types import OrderReportType
from app.integration.amazon.reports.service import ReportsService

logger = logging.getLogger(__name__)

MAX_RANGE = timedelta(days=30)


@dataclass
class OrderItemRow:
    """One order item from the report. `raw` keeps every column, since they vary by marketplace."""

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
    raw: dict[str, str]

    @classmethod
    def from_report_row(cls, row: dict) -> "OrderItemRow | None":
        """Parse one report row. None for rows without an order id / order item id."""
        r = normalize_row(row)
        order_id = to_str(r.get("amazon-order-id"), 50)
        order_item_id = to_str(r.get("order-item-id"), 50)
        if not order_id or not order_item_id:
            return None
        return cls(
            amazon_order_id=order_id,
            order_item_id=order_item_id,
            merchant_order_id=to_str(r.get("merchant-order-id"), 50),
            purchase_date=to_datetime(r.get("purchase-date")),
            last_updated_date=to_datetime(r.get("last-updated-date")),
            order_status=to_str(r.get("order-status"), 50),
            fulfillment_channel=to_str(r.get("fulfillment-channel"), 50),
            sales_channel=to_str(r.get("sales-channel"), 100),
            ship_service_level=to_str(r.get("ship-service-level"), 50),
            product_name=to_str(r.get("product-name"), 500),
            sku=to_str(r.get("sku"), 255) or "",
            asin=to_str(r.get("asin"), 20),
            item_status=to_str(r.get("item-status"), 50),
            quantity=to_int(r.get("quantity")),
            currency=to_str(r.get("currency"), 3),
            item_price=to_decimal(r.get("item-price")),
            item_tax=to_decimal(r.get("item-tax")),
            shipping_price=to_decimal(r.get("shipping-price")),
            shipping_tax=to_decimal(r.get("shipping-tax")),
            gift_wrap_price=to_decimal(r.get("gift-wrap-price")),
            gift_wrap_tax=to_decimal(r.get("gift-wrap-tax")),
            item_promotion_discount=to_decimal(r.get("item-promotion-discount")),
            ship_promotion_discount=to_decimal(r.get("ship-promotion-discount")),
            ship_city=to_str(r.get("ship-city"), 100),
            ship_state=to_str(r.get("ship-state"), 100),
            ship_postal_code=to_str(r.get("ship-postal-code"), 20),
            ship_country=to_str(r.get("ship-country"), 2),
            promotion_ids=to_str(r.get("promotion-ids")),
            is_business_order=to_bool(r.get("is-business-order")),
            raw=r,
        )


class AllOrdersByOrderDateReport:
    """Requests, waits for and parses GET_FLAT_FILE_ALL_ORDERS_DATA_BY_ORDER_DATE_GENERAL."""

    REPORT_TYPE = OrderReportType.GET_FLAT_FILE_ALL_ORDERS_DATA_BY_ORDER_DATE_GENERAL

    def __init__(self, credentials: AmazonCredentials | None = None, service: ReportsService | None = None):
        self.service = service or ReportsService(credentials)

    def request(
        self,
        start: datetime,
        end: datetime,
        marketplace_ids: Sequence[str] | None = None,
    ) -> str:
        """Ask Amazon to generate the report for orders placed in [start, end]. Returns the reportId."""
        if end < start:
            raise ValueError("end must be on or after start")
        if end - start > MAX_RANGE:
            raise ValueError(f"{self.REPORT_TYPE.value} covers at most {MAX_RANGE.days} days per request")
        return self.service.create_report(
            self.REPORT_TYPE,
            marketplace_ids=marketplace_ids,
            data_start_time=start,
            data_end_time=end,
        )

    def wait(
        self,
        report_id: str,
        poll_interval: float = 30.0,
        timeout: float = 60 * 60,
        on_status: Callable[[str], None] | None = None,
    ) -> Report:
        """Block until Amazon has finished the report. Raises ReportProcessingError on FATAL/CANCELLED."""
        return self.service.wait_for_report(
            report_id, poll_interval=poll_interval, timeout=timeout, on_status=on_status
        )

    def download_rows(self, report: Report | str) -> list[OrderItemRow]:
        """Download a DONE report and parse it into order item rows."""
        result = self.service.download_report(report)
        rows = [row for row in map(OrderItemRow.from_report_row, result.rows()) if row]
        logger.info("Parsed %d order items from report %s", len(rows), result.report.report_id)
        return rows
