"""GET_MERCHANT_LISTINGS_ALL_DATA

Tab-delimited flat file with one row per listing (SKU) of the marketplace, active and inactive.
It is a snapshot of the listings when the report is generated: dataStartTime/dataEndTime don't apply.
Docs: https://developer-docs.amazon.com/sp-api/docs/report-type-values-inventory

    report = AllListingsReport(AmazonCredentials.for_marketplace(Marketplace.US))
    report_id = report.request(marketplace_ids=[Marketplace.US.marketplace_id])  # returns immediately
    rows = report.download_rows(report.wait(report_id))                          # blocking: background task
"""

import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from decimal import Decimal

from spapi.models.reports_v2021_06_30 import Report

from app.integration.amazon.config import AmazonCredentials
from app.integration.amazon.reports.fields import normalize_row, to_decimal, to_int, to_str
from app.integration.amazon.reports.listing.report_types import ListingReportType
from app.integration.amazon.reports.service import ReportsService

logger = logging.getLogger(__name__)


@dataclass
class ListingRow:
    """One listing from the report. `raw` keeps every column, since they vary by marketplace."""

    seller_sku: str
    listing_id: str | None
    item_name: str | None
    item_description: str | None
    asin: str | None
    product_id: str | None
    product_id_type: str | None
    price: Decimal | None
    quantity: int | None
    pending_quantity: int | None
    open_date: str | None
    image_url: str | None
    item_condition: str | None
    item_note: str | None
    fulfillment_channel: str | None
    merchant_shipping_group: str | None
    status: str | None
    raw: dict[str, str]

    @classmethod
    def from_report_row(cls, row: dict) -> "ListingRow | None":
        """Parse one report row. None for rows without a seller SKU."""
        r = normalize_row(row)
        sku = to_str(r.get("seller-sku"), 255)
        if not sku:
            return None
        return cls(
            seller_sku=sku,
            listing_id=to_str(r.get("listing-id"), 50),
            item_name=to_str(r.get("item-name"), 500),
            item_description=to_str(r.get("item-description")),
            asin=to_str(r.get("asin1"), 20),
            product_id=to_str(r.get("product-id"), 50),
            product_id_type=to_str(r.get("product-id-type"), 10),
            price=to_decimal(r.get("price")),
            quantity=to_int(r.get("quantity")),
            pending_quantity=to_int(r.get("pending-quantity")),
            open_date=to_str(r.get("open-date"), 50),  # e.g. "2024-01-15 10:22:33 PST"
            image_url=to_str(r.get("image-url"), 1000),
            item_condition=to_str(r.get("item-condition"), 10),
            item_note=to_str(r.get("item-note")),
            fulfillment_channel=to_str(r.get("fulfillment-channel"), 50),
            merchant_shipping_group=to_str(r.get("merchant-shipping-group"), 255),
            status=to_str(r.get("status"), 20),
            raw=r,
        )


class AllListingsReport:
    """Requests, waits for and parses GET_MERCHANT_LISTINGS_ALL_DATA."""

    REPORT_TYPE = ListingReportType.GET_MERCHANT_LISTINGS_ALL_DATA

    def __init__(self, credentials: AmazonCredentials | None = None, service: ReportsService | None = None):
        self.service = service or ReportsService(credentials)

    def request(self, marketplace_ids: Sequence[str] | None = None) -> str:
        """Ask Amazon to generate a snapshot of the marketplace's listings. Returns the reportId."""
        return self.service.create_report(self.REPORT_TYPE, marketplace_ids=marketplace_ids)

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

    def download_rows(self, report: Report | str) -> list[ListingRow]:
        """Download a DONE report and parse it into listing rows."""
        result = self.service.download_report(report)
        rows = [row for row in map(ListingRow.from_report_row, result.rows()) if row]
        logger.info("Parsed %d listings from report %s", len(rows), result.report.report_id)
        return rows
