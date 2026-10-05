from datetime import datetime
from typing import Literal

from app.integration.amazon.marketplaces import Region
from app.schemas.base import CamelModel
from app.schemas.report import SkippedPeriodOut

DataKioskSyncStatus = Literal["QUEUED", "PROCESSING", "SYNCED", "FAILED", "CANCELLED"]


class DataKioskQueryOut(CamelModel):
    """One query in the Data Kiosk queue and the outcome of storing its rows (any query type)."""

    id: int
    query_id: str | None  # Amazon queryId, once submitted
    query_type: str
    region: Region
    marketplace_id: str
    data_start_time: datetime
    data_end_time: datetime
    processing_status: str | None  # Amazon's status
    data_document_id: str | None  # first result page; None when there was no data
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


class DataKioskQueueOut(CamelModel):
    current: DataKioskQueryOut | None  # the one query being processed now
    pending: list[DataKioskQueryOut]  # waiting, in the order they will run
    counts: dict[str, int]  # every query ever queued, by sync status (QUEUED, PROCESSING, SYNCED, ...)


class DataKioskBatchOut(CamelModel):
    """Result of queuing several Data Kiosk queries at once."""

    queued: list[DataKioskQueryOut]
    skipped: list[SkippedPeriodOut]  # e.g. the same query is already queued or processing
