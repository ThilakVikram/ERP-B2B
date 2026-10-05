"""GET_FLAT_FILE_ALL_ORDERS_DATA_BY_ORDER_DATE_GENERAL: orders placed in a given period.

Requests go through the central report queue (report_queue_service), which runs one report
at a time; a longer period can be scheduled as consecutive reports of 1-30 days each. Rows are bulk inserted into
amazon_intg_order_report_items in chunks; order items (order id + order item id) already stored are skipped.
"""

from collections.abc import Callable
from dataclasses import asdict

from spapi.models.reports_v2021_06_30 import Report
from sqlalchemy.orm import Session

from app.config import REPORT_MAX_RANGE_DAYS
from app.integration.amazon import AmazonCredentials, Region
from app.integration.amazon.reports.order import AllOrdersByOrderDateReport
from app.models.integration.amazon.reports.amazon_report import AmazonReport
from app.repositories import amazon_report_repository, order_report_item_repository
from app.schemas.order_report import (
    OrderReportCreateIn,
    OrderReportItemOut,
    OrderItemsSummaryOut,
)
from app.schemas.report import AmazonReportOut, ReportBatchOut, ReportCoverageOut, ReportScheduleIn
from app.services.report_queue_service import (
    ReportHandler,
    coverage,
    schedule_periods,
    get_marketplace,
    now,
    report_queue,
    split_period,
)

REPORT_TYPE = AllOrdersByOrderDateReport.REPORT_TYPE.value


def _client(report: AmazonReport) -> AllOrdersByOrderDateReport:
    return AllOrdersByOrderDateReport(AmazonCredentials.for_marketplace(get_marketplace(report.marketplace_id)))


class AllOrdersByOrderDateHandler(ReportHandler):
    report_type = REPORT_TYPE

    def request(self, report: AmazonReport) -> str:
        # A request for today may have waited in the queue; Amazon rejects an end time in the future.
        end = min(report.data_end_time, now())
        return _client(report).request(report.data_start_time, end, marketplace_ids=[report.marketplace_id])

    def wait(self, report: AmazonReport, on_status: Callable[[str], None]) -> Report:
        return _client(report).wait(report.report_id, on_status=on_status)

    def store(self, db: Session, report: AmazonReport, done: Report) -> tuple[int, int]:
        rows = [asdict(row) for row in _client(report).download_rows(done)]
        inserted = order_report_item_repository.insert_new(db, report.region, report.marketplace_id, report.id, rows)
        return len(rows), inserted


report_queue.register(AllOrdersByOrderDateHandler())


def request_report(db: Session, payload: OrderReportCreateIn, requested_by_id: int) -> AmazonReportOut:
    """Queue the report for the period. The queue worker requests, downloads and stores it."""
    # The schema caps the range at REPORT_MAX_RANGE_DAYS, so this is a single period.
    [(start, end)] = split_period(payload.start_date, payload.end_date, days=REPORT_MAX_RANGE_DAYS)
    return report_queue.enqueue(db, REPORT_TYPE, payload.marketplace_id, start, end, requested_by_id=requested_by_id)


def schedule_reports(db: Session, payload: ReportScheduleIn, requested_by_id: int) -> ReportBatchOut:
    """Queue the period as consecutive reports of `partition_days` days (see schedule_periods)."""
    return schedule_periods(db, REPORT_TYPE, payload, requested_by_id)


# ---------- Reads ----------


def list_reports(db: Session, region: Region | None = None, marketplace_id: str | None = None) -> list[AmazonReportOut]:
    rows = amazon_report_repository.list_all(db, region.value if region else None, marketplace_id, REPORT_TYPE)
    return [AmazonReportOut.model_validate(r) for r in rows]


def list_order_items(
    db: Session, region: Region | None = None, marketplace_id: str | None = None, limit: int = 100, offset: int = 0
) -> list[OrderReportItemOut]:
    rows = order_report_item_repository.list_all(db, region.value if region else None, marketplace_id, limit, offset)
    return [OrderReportItemOut.model_validate(r) for r in rows]


def summarize_order_items(db: Session) -> list[OrderItemsSummaryOut]:
    return [OrderItemsSummaryOut(**row) for row in order_report_item_repository.summary_by_marketplace(db)]


def get_coverage(db: Session, marketplace_id: str) -> ReportCoverageOut:
    """Days of the marketplace already in the queue or already fetched."""
    return coverage(db, REPORT_TYPE, marketplace_id)
