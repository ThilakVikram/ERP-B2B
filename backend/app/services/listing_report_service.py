"""GET_MERCHANT_LISTINGS_ALL_DATA: a snapshot of every listing (SKU) of a marketplace.

Requests go through the central report queue (report_queue_service), which runs one report
at a time. Rows are bulk upserted into amazon_intg_merchant_listings in chunks: new SKUs are inserted and
stored SKUs are updated to the latest snapshot.
"""

from collections.abc import Callable
from dataclasses import asdict
from datetime import datetime, time

from fastapi import HTTPException, status
from spapi.models.reports_v2021_06_30 import Report
from sqlalchemy.orm import Session

from app.integration.amazon import AmazonCredentials, Region
from app.integration.amazon.reports.listing import AllListingsReport
from app.models.integration.amazon.reports.amazon_report import AmazonReport
from app.repositories import merchant_listing_repository
from app.schemas.listing_report import ListingReportCreateIn, ListingsSummaryOut, MerchantListingOut
from app.schemas.report import ReportBatchOut, SkippedPeriodOut
from app.services.report_queue_service import ReportHandler, get_marketplace, now, report_queue

REPORT_TYPE = AllListingsReport.REPORT_TYPE.value


def _client(report: AmazonReport) -> AllListingsReport:
    return AllListingsReport(AmazonCredentials.for_marketplace(get_marketplace(report.marketplace_id)))


class AllListingsHandler(ReportHandler):
    report_type = REPORT_TYPE

    def request(self, report: AmazonReport) -> str:
        return _client(report).request(marketplace_ids=[report.marketplace_id])

    def wait(self, report: AmazonReport, on_status: Callable[[str], None]) -> Report:
        return _client(report).wait(report.report_id, on_status=on_status)

    def store(self, db: Session, report: AmazonReport, done: Report) -> tuple[int, int]:
        rows = [asdict(row) for row in _client(report).download_rows(done)]
        inserted = merchant_listing_repository.upsert_all(db, report.region, report.marketplace_id, report.id, rows)
        # skipped_count on the report = SKUs that were already stored and got updated.
        return len(rows), inserted


report_queue.register(AllListingsHandler())


def request_reports(db: Session, payload: ListingReportCreateIn, requested_by_id: int) -> ReportBatchOut:
    """Queue one listings snapshot per marketplace.

    The snapshot has no data period; the request is recorded against today (UTC), so a marketplace
    can't have two snapshots queued at once for the same day. Those come back under `skipped`.
    """
    today = now().date()
    start, end = datetime.combine(today, time.min), datetime.combine(today, time(23, 59, 59))
    queued, skipped = [], []
    for marketplace_id in dict.fromkeys(payload.marketplace_ids):
        try:
            queued.append(report_queue.enqueue(db, REPORT_TYPE, marketplace_id, start, end, requested_by_id=requested_by_id))
        except HTTPException as exc:
            if exc.status_code != status.HTTP_409_CONFLICT:
                raise
            skipped.append(SkippedPeriodOut(start_date=today, end_date=today, reason=f"{marketplace_id}: {exc.detail}"))
    return ReportBatchOut(queued=queued, skipped=skipped)


# ---------- Reads ----------


def summarize_listings(db: Session) -> list[ListingsSummaryOut]:
    return [ListingsSummaryOut(**row) for row in merchant_listing_repository.summary_by_marketplace(db)]


def list_listings(
    db: Session, region: Region | None = None, marketplace_id: str | None = None, limit: int = 100, offset: int = 0
) -> list[MerchantListingOut]:
    rows = merchant_listing_repository.list_all(db, region.value if region else None, marketplace_id, limit, offset)
    return [MerchantListingOut.model_validate(r) for r in rows]
