from datetime import date, datetime, timezone
from typing import Literal

from pydantic import Field, model_validator

from app.config import REPORT_MAX_RANGE_DAYS

from app.integration.amazon.marketplaces import Region
from app.schemas.base import CamelModel

MAX_SCHEDULE_RANGE_DAYS = 366  # one schedule covers at most a year


ReportSyncStatus = Literal["QUEUED", "PROCESSING", "SYNCED", "FAILED", "CANCELLED"]


class AmazonReportOut(CamelModel):
    """One report request in the queue and the outcome of storing its rows (any report type)."""

    id: int
    report_id: str | None  # Amazon reportId, once requested
    report_type: str
    region: Region
    marketplace_id: str
    data_start_time: datetime
    data_end_time: datetime
    processing_status: str | None  # Amazon's status
    sync_status: str  # QUEUED | PROCESSING | SYNCED | FAILED | CANCELLED
    row_count: int
    inserted_count: int
    skipped_count: int
    error: str | None
    requested_by_id: int | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    queue_position: int | None = None  # 1 = next to run; only while QUEUED


class ReportQueueOut(CamelModel):
    current: AmazonReportOut | None  # the one report being processed now
    pending: list[AmazonReportOut]  # waiting, in the order they will run
    counts: dict[str, int]  # every request ever queued, by sync status (QUEUED, PROCESSING, SYNCED, ...)


class SkippedPeriodOut(CamelModel):
    start_date: date
    end_date: date
    reason: str


class ReportBatchOut(CamelModel):
    """Result of queuing several report requests at once."""

    queued: list[AmazonReportOut]
    skipped: list[SkippedPeriodOut]  # e.g. the same request is already queued or processing


class DatePeriodOut(CamelModel):
    start_date: date
    end_date: date  # inclusive


class ReportCoverageOut(CamelModel):
    """Days of one marketplace covered by requests of a type, per sync status (as in the request
    history), each merged into continuous periods."""

    queued: list[DatePeriodOut]
    processing: list[DatePeriodOut]
    synced: list[DatePeriodOut]  # fetched, including periods Amazon had no data for
    failed: list[DatePeriodOut]
    cancelled: list[DatePeriodOut]


class ReportScheduleIn(CamelModel):
    """A period (whole days, UTC) queued as consecutive requests of `partitionDays` days each,
    starting at startDate; the last one may be shorter. Used by every date-range report / query."""

    marketplace_id: str
    start_date: date
    end_date: date  # inclusive
    partition_days: int = Field(ge=1, le=REPORT_MAX_RANGE_DAYS)

    @model_validator(mode="after")
    def _check_date_range(self) -> "ReportScheduleIn":
        if self.end_date < self.start_date:
            raise ValueError("endDate must be on or after startDate")
        if self.end_date > datetime.now(timezone.utc).date():
            raise ValueError("endDate cannot be in the future")
        days = (self.end_date - self.start_date).days + 1
        if days > MAX_SCHEDULE_RANGE_DAYS:
            raise ValueError(f"A schedule can cover at most {MAX_SCHEDULE_RANGE_DAYS} days (got {days})")
        return self
