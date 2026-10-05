"""Reports API (2021-06-30) wrapper built on amzn-sp-api.

Generic plumbing only: it knows nothing about individual report types. Each report type lives
in its category package (e.g. reports/order/) and uses this service to request and download it.

    service = ReportsService(AmazonCredentials.for_marketplace(Marketplace.IN))
    report_id = service.create_report("GET_FLAT_FILE_ALL_ORDERS_DATA_BY_ORDER_DATE_GENERAL", ...)

fetch_report() / wait_for_report() block while Amazon processes the report (seconds to
tens of minutes). Run them in a background worker, not inside a request handler.
"""

import logging
import time
from collections.abc import Callable, Iterator, Sequence
from datetime import datetime, timezone
from enum import Enum

from spapi import ApiClient
from spapi.api.reports_v2021_06_30.reports_api import ReportsApi
from spapi.models.reports_v2021_06_30 import (
    CreateReportScheduleSpecification,
    CreateReportSpecification,
    Report,
    ReportDocument,
    ReportSchedule,
)

from app.integration.amazon.client import build_api_client, call_with_retry
from app.integration.amazon.config import AmazonCredentials
from app.integration.amazon.exceptions import (
    AmazonConfigError,
    ReportProcessingError,
    ReportTimeoutError,
)
from app.integration.amazon.reports.document import ReportResult, decode_content, download_document

logger = logging.getLogger(__name__)


class ProcessingStatus:
    CANCELLED = "CANCELLED"
    DONE = "DONE"
    FATAL = "FATAL"
    IN_PROGRESS = "IN_PROGRESS"
    IN_QUEUE = "IN_QUEUE"

    TERMINAL = frozenset({CANCELLED, DONE, FATAL})


def _utc(dt: datetime | None) -> datetime | None:
    """SP-API wants ISO 8601 with offset; treat naive datetimes as UTC."""
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


ReportTypeValue = str | Enum


def _value(report_type: ReportTypeValue) -> str:
    return report_type.value if isinstance(report_type, Enum) else report_type


class ReportsService:
    """One instance per seller account (credentials). Safe to reuse across calls."""

    def __init__(
        self,
        credentials: AmazonCredentials | None = None,
        api_client: ApiClient | None = None,
    ):
        self.credentials = credentials or AmazonCredentials.from_env()
        self._api_client = api_client
        self._api: ReportsApi | None = None

    @property
    def api(self) -> ReportsApi:
        # Built lazily: creating the SDK client performs an LWA token request.
        if self._api is None:
            self._api = ReportsApi(self._api_client or build_api_client(self.credentials))
        return self._api

    def _marketplaces(self, marketplace_ids: Sequence[str] | None) -> list[str]:
        ids = list(marketplace_ids or self.credentials.marketplace_ids)
        if not ids:
            raise AmazonConfigError(
                f"No marketplace_ids given and AMAZON_SP_API_{self.credentials.region.value}_MARKETPLACE_IDS is not set"
            )
        return ids

    # ---------- Reports ----------

    def create_report(
        self,
        report_type: ReportTypeValue,
        marketplace_ids: Sequence[str] | None = None,
        data_start_time: datetime | None = None,
        data_end_time: datetime | None = None,
        report_options: dict[str, str] | None = None,
    ) -> str:
        """Request a report. Returns the reportId."""
        body = CreateReportSpecification(
            report_type=_value(report_type),
            marketplace_ids=self._marketplaces(marketplace_ids),
            data_start_time=_utc(data_start_time),
            data_end_time=_utc(data_end_time),
            report_options=report_options,
        )
        resp = call_with_retry(self.api.create_report, body)
        logger.info("Requested %s report %s", _value(report_type), resp.report_id)
        return resp.report_id

    def get_report(self, report_id: str) -> Report:
        return call_with_retry(self.api.get_report, report_id)

    def get_reports(
        self,
        report_types: Sequence[ReportTypeValue],
        processing_statuses: Sequence[str] | None = None,
        marketplace_ids: Sequence[str] | None = None,
        created_since: datetime | None = None,
        created_until: datetime | None = None,
        page_size: int = 100,
    ) -> Iterator[Report]:
        """Yield every matching report across all pages (reports are kept for 90 days)."""
        kwargs = {
            "report_types": [_value(t) for t in report_types],
            "page_size": page_size,
        }
        if processing_statuses:
            kwargs["processing_statuses"] = list(processing_statuses)
        if marketplace_ids:
            kwargs["marketplace_ids"] = list(marketplace_ids)
        if created_since:
            kwargs["created_since"] = _utc(created_since)
        if created_until:
            kwargs["created_until"] = _utc(created_until)

        while True:
            resp = call_with_retry(self.api.get_reports, **kwargs)
            yield from resp.reports or []
            if not resp.next_token:
                return
            # nextToken must be sent on its own.
            kwargs = {"next_token": resp.next_token}

    def cancel_report(self, report_id: str) -> None:
        """Cancel a report that is still IN_QUEUE."""
        call_with_retry(self.api.cancel_report, report_id)

    def wait_for_report(
        self,
        report_id: str,
        poll_interval: float = 30.0,
        timeout: float = 60 * 60,
        on_status: Callable[[str], None] | None = None,
    ) -> Report:
        """Poll until the report is DONE. Raises ReportProcessingError on FATAL/CANCELLED.

        `on_status` is called with Amazon's processing status each time it changes.
        """
        deadline = time.monotonic() + timeout
        last_status = None
        while True:
            report = self.get_report(report_id)
            status = report.processing_status
            if on_status and status != last_status:
                on_status(status)
            last_status = status
            if status == ProcessingStatus.DONE:
                return report
            if status in ProcessingStatus.TERMINAL:
                raise ReportProcessingError(report_id, status, self._fatal_details(report))
            if time.monotonic() + poll_interval > deadline:
                raise ReportTimeoutError(
                    f"Report {report_id} still {status} after {timeout:.0f}s"
                )
            logger.debug("Report %s is %s, polling again in %.0fs", report_id, status, poll_interval)
            time.sleep(poll_interval)

    def _fatal_details(self, report: Report) -> str | None:
        # A FATAL report may carry a document describing why it failed.
        if not report.report_document_id:
            return None
        try:
            doc = self.get_report_document(report.report_document_id)
            content, charset = download_document(doc)
            return decode_content(content, charset)[:2000]
        except Exception:
            logger.exception("Could not fetch error document for report %s", report.report_id)
            return None

    # ---------- Documents ----------

    def get_report_document(self, report_document_id: str) -> ReportDocument:
        """Document metadata incl. a pre-signed URL that expires after 5 minutes."""
        return call_with_retry(self.api.get_report_document, report_document_id)

    def download_report(self, report: Report | str) -> ReportResult:
        """Download a DONE report (Report object or reportId)."""
        if isinstance(report, str):
            report = self.get_report(report)
        if not report.report_document_id:
            raise ReportProcessingError(
                report.report_id, report.processing_status, "report has no document"
            )
        return self.download_document(report.report_document_id, report=report)

    def download_document(self, report_document_id: str, report: Report | None = None) -> ReportResult:
        document = self.get_report_document(report_document_id)
        content, charset = download_document(document)
        return ReportResult(report=report, document=document, content=content, encoding=charset)

    def fetch_report(
        self,
        report_type: ReportTypeValue,
        marketplace_ids: Sequence[str] | None = None,
        data_start_time: datetime | None = None,
        data_end_time: datetime | None = None,
        report_options: dict[str, str] | None = None,
        poll_interval: float = 30.0,
        timeout: float = 60 * 60,
    ) -> ReportResult:
        """Create a report, wait for it to finish and download it. Blocking."""
        report_id = self.create_report(
            report_type,
            marketplace_ids=marketplace_ids,
            data_start_time=data_start_time,
            data_end_time=data_end_time,
            report_options=report_options,
        )
        report = self.wait_for_report(report_id, poll_interval=poll_interval, timeout=timeout)
        return self.download_report(report)

    def fetch_latest_report(
        self,
        report_type: ReportTypeValue,
        marketplace_ids: Sequence[str] | None = None,
        created_since: datetime | None = None,
    ) -> ReportResult | None:
        """Download the newest DONE report of a type (e.g. settlement reports). None if none exist."""
        reports = self.get_reports(
            [report_type],
            processing_statuses=[ProcessingStatus.DONE],
            marketplace_ids=marketplace_ids,
            created_since=created_since,
        )
        latest = max(reports, key=lambda r: r.created_time, default=None)
        return self.download_report(latest) if latest else None

    # ---------- Schedules ----------

    def create_report_schedule(
        self,
        report_type: ReportTypeValue,
        period: str,
        marketplace_ids: Sequence[str] | None = None,
        report_options: dict[str, str] | None = None,
        next_report_creation_time: datetime | None = None,
    ) -> str:
        """Schedule recurring reports. `period` is ISO 8601, e.g. PT1H, P1D, P7D, P1M."""
        body = CreateReportScheduleSpecification(
            report_type=_value(report_type),
            marketplace_ids=self._marketplaces(marketplace_ids),
            report_options=report_options,
            period=period,
            next_report_creation_time=_utc(next_report_creation_time),
        )
        return call_with_retry(self.api.create_report_schedule, body).report_schedule_id

    def get_report_schedules(self, report_types: Sequence[ReportTypeValue]) -> list[ReportSchedule]:
        resp = call_with_retry(self.api.get_report_schedules, [_value(t) for t in report_types])
        return resp.report_schedules or []

    def get_report_schedule(self, report_schedule_id: str) -> ReportSchedule:
        return call_with_retry(self.api.get_report_schedule, report_schedule_id)

    def cancel_report_schedule(self, report_schedule_id: str) -> None:
        call_with_retry(self.api.cancel_report_schedule, report_schedule_id)
