"""Queue for every SP-API report request (Reports API 2021-06-30): one report at a time, end to end.

All report features go through `report_queue`; nothing else may call the Reports API. It is a
JobQueue (job_queue_service) over amazon_intg_reports with its own worker; Data Kiosk queries have
their own queue and table (data_kiosk_queue_service).

Statuses (amazon_intg_reports.sync_status): QUEUED -> PROCESSING -> SYNCED | FAILED, or CANCELLED
while still QUEUED.
"""

from spapi.models.reports_v2021_06_30 import Report
from sqlalchemy.orm import Session

from app.models.integration.amazon.reports.amazon_report import AmazonReport
from app.repositories import amazon_report_repository
from app.schemas.report import (
    AmazonReportOut,
    ReportBatchOut,
    ReportCoverageOut,
    ReportQueueOut,
    ReportScheduleIn,
)
from app.services.job_queue_service import (  # noqa: F401 — re-exported for the report services
    JobHandler,
    JobQueue,
    JobTable,
    get_marketplace,
    list_report_marketplaces,
    now,
    split_period,
)

report_queue = JobQueue(
    JobTable(
        repository=amazon_report_repository,
        type_field="report_type",
        amazon_id_field="report_id",
        document_field="report_document_id",
        noun="report",
        lock_name="itrend_report_queue_worker",
        job_out=AmazonReportOut,
        queue_out=ReportQueueOut,
        batch_out=ReportBatchOut,
    )
)


class ReportHandler(JobHandler):
    """The report-type specific steps; `report_type` is the Reports API reportType it handles."""

    report_type: str

    @property
    def job_type(self) -> str:
        return self.report_type

    def document_id(self, done: Report) -> str | None:
        return done.report_document_id


def list_reports(
    db: Session,
    region: str | None = None,
    marketplace_id: str | None = None,
    report_types: list[str] | None = None,
    sync_statuses: list[str] | None = None,
    limit: int = 100,
) -> list[AmazonReportOut]:
    rows: list[AmazonReport] = amazon_report_repository.list_all(
        db, region, marketplace_id, report_types, limit, sync_statuses
    )
    return [AmazonReportOut.model_validate(r) for r in rows]


def coverage(db: Session, report_type: str, marketplace_id: str) -> ReportCoverageOut:
    """Days of the marketplace already in the queue or already fetched for a report type."""
    return report_queue.coverage(db, report_type, marketplace_id)


def schedule_periods(db: Session, report_type: str, payload: ReportScheduleIn, requested_by_id: int) -> ReportBatchOut:
    """Queue the period as consecutive reports of `partition_days` days (see JobQueue.schedule_periods)."""
    return report_queue.schedule_periods(db, report_type, payload, requested_by_id)
