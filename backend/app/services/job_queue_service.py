"""Generic queue for asynchronous Amazon jobs (Reports API reports, Data Kiosk queries): one job at a
time per queue, end to end.

Each queue keeps its jobs in its own table (see JobTable) and has its own worker:
    - report_queue_service.report_queue: amazon_intg_reports (Reports API)
    - data_kiosk_queue_service.data_kiosk_queue: amazon_intg_data_kiosk_queries (Data Kiosk API)
The two APIs have separate Amazon rate limits, so the queues run independently of each other.

How a queue works:
    1. A feature service registers a JobHandler for its job type (at import).
    2. enqueue() only records the request as QUEUED (no Amazon call), rejecting duplicates and
       marketplaces the seller doesn't participate in (amazon_intg_marketplace_participations table).
    3. A single worker thread takes the oldest QUEUED job and runs it to the end —
       request, wait for Amazon, download, store — before starting the next one.

Only one worker per queue runs across all app processes (MySQL GET_LOCK), so running several
uvicorn workers can't process two jobs of a queue at once. A job interrupted by a restart is
resumed: if Amazon already has it, the worker keeps waiting on the same Amazon ID instead of
requesting again.

Statuses (sync_status): QUEUED -> PROCESSING -> SYNCED | FAILED, or CANCELLED while still QUEUED.
"""

import logging
import threading
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from types import ModuleType
from typing import Any

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, engine
from app.integration.amazon import Marketplace, ReportProcessingError
from app.integration.amazon.reports import ProcessingStatus
from app.repositories import marketplace_participation_repository
from app.schemas.report import DatePeriodOut, ReportCoverageOut, ReportScheduleIn, SkippedPeriodOut
from app.schemas.seller import MarketplaceParticipationOut

logger = logging.getLogger(__name__)

QUEUED = "QUEUED"
PROCESSING = "PROCESSING"
SYNCED = "SYNCED"
FAILED = "FAILED"
CANCELLED = "CANCELLED"
ACTIVE = [QUEUED, PROCESSING]
ALL_STATUSES = [QUEUED, PROCESSING, SYNCED, FAILED, CANCELLED]

POLL_SECONDS = 5  # how often an idle worker checks for jobs queued by another process


def now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


_MARKETPLACES = {m.marketplace_id: m for m in Marketplace}


def get_marketplace(marketplace_id: str) -> Marketplace:
    marketplace = _MARKETPLACES.get(marketplace_id)
    if marketplace is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown marketplace ID {marketplace_id!r}",
        )
    return marketplace


def list_report_marketplaces(db: Session, region: str | None = None) -> list[MarketplaceParticipationOut]:
    """Marketplaces jobs can be requested for: ones the seller participates in (from the last
    Sellers sync) that are Amazon SP-API marketplaces (not e.g. "Non-Amazon US" or "Amazon Pay")."""
    rows = marketplace_participation_repository.list_participating(db, region)
    return [MarketplaceParticipationOut.model_validate(r) for r in rows if r.marketplace_id in _MARKETPLACES]


def get_report_marketplace(db: Session, marketplace_id: str) -> Marketplace:
    marketplace = get_marketplace(marketplace_id)
    if marketplace_participation_repository.get_participating(db, marketplace_id) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Marketplace {marketplace_id} is not one this seller participates in. "
                "Sync marketplace participations for its region first."
            ),
        )
    return marketplace


def split_period(start_date: date, end_date: date, days: int) -> list[tuple[datetime, datetime]]:
    """Whole days in UTC split into consecutive periods of at most `days` days, each
    [first day 00:00:00, last day 23:59:59]."""
    periods = []
    day = start_date
    while day <= end_date:
        last = min(day + timedelta(days=days - 1), end_date)
        periods.append((datetime.combine(day, time.min), datetime.combine(last, time(23, 59, 59))))
        day = last + timedelta(days=1)
    return periods


def _merge(periods: list[tuple[date, date]]) -> list[DatePeriodOut]:
    """Merge overlapping or adjacent day periods."""
    merged: list[list[date]] = []
    for start, end in sorted(periods):
        if merged and start <= merged[-1][1] + timedelta(days=1):
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return [DatePeriodOut(start_date=s, end_date=e) for s, e in merged]


@dataclass(frozen=True)
class JobTable:
    """The table a queue keeps its jobs in, and that table's names for the Amazon-side fields.

    `repository` is a repository module with the queue functions (create, get, update,
    list_by_sync_status, next_queued, find_active_duplicate, count_queued_before, set_sync_status,
    count_by_sync_status, list_periods) — see amazon_report_repository.
    """

    repository: ModuleType
    type_field: str  # job type column, e.g. "report_type"
    amazon_id_field: str  # Amazon's ID of the job, e.g. "report_id"
    document_field: str  # Amazon's result document ID, e.g. "report_document_id"
    noun: str  # for messages, e.g. "report"
    lock_name: str  # MySQL lock held by the one worker of this queue
    job_out: type[BaseModel]  # API schema of one job
    queue_out: type[BaseModel]  # API schema of the queue: current, pending, counts
    batch_out: type[BaseModel]  # API schema of a schedule result: queued, skipped


class JobHandler(ABC):
    """The job-type specific steps. The queue owns ordering and status bookkeeping."""

    job_type: str

    @abstractmethod
    def request(self, job: Any) -> str:
        """Ask Amazon to create the job for its marketplace and period. Returns Amazon's ID."""

    @abstractmethod
    def wait(self, job: Any, on_status: Callable[[str], None]) -> Any:
        """Block until Amazon has finished the job, calling on_status as Amazon's status changes.
        Raises ReportProcessingError (or a subclass) on FATAL/CANCELLED."""

    @abstractmethod
    def store(self, db: Session, job: Any, done: Any) -> tuple[int, int]:
        """Download the finished job's result and store its rows. Returns (row count, rows inserted)."""

    @abstractmethod
    def document_id(self, done: Any) -> str | None:
        """ID of the finished job's result document."""


class JobQueue:
    def __init__(self, table: JobTable) -> None:
        self.table = table
        self._repo = table.repository
        self._handlers: dict[str, JobHandler] = {}
        self._enqueue_lock = threading.Lock()  # duplicate check + insert, within this process
        self._wake = threading.Event()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def register(self, handler: JobHandler) -> None:
        self._handlers[handler.job_type] = handler

    def _type(self, job: Any) -> str:
        return getattr(job, self.table.type_field)

    # ---------- Requests (called from API services) ----------

    def enqueue(
        self,
        db: Session,
        job_type: str,
        marketplace_id: str,
        data_start_time: datetime,
        data_end_time: datetime,
        requested_by_id: int | None = None,
        **extra: Any,  # further columns of the job table, e.g. report_options
    ) -> BaseModel:
        """Add a job to the queue. 409 if the same job is already queued or processing;
        400 if the seller doesn't participate in the marketplace."""
        if job_type not in self._handlers:
            raise ValueError(f"No JobHandler registered for {job_type}")
        marketplace = get_report_marketplace(db, marketplace_id)
        with self._enqueue_lock:
            duplicate = self._repo.find_active_duplicate(
                db, ACTIVE, job_type, marketplace.marketplace_id, data_start_time, data_end_time
            )
            if duplicate is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"The same {self.table.noun} is already {duplicate.sync_status.lower()} (request {duplicate.id})",
                )
            job = self._repo.create(
                db,
                **{self.table.type_field: job_type},
                region=marketplace.region.value,
                marketplace_id=marketplace.marketplace_id,
                data_start_time=data_start_time,
                data_end_time=data_end_time,
                sync_status=QUEUED,
                requested_by_id=requested_by_id,
                **extra,
            )
        self._wake.set()
        logger.info("Queued %s for %s as %s request %s", job_type, marketplace.marketplace_id, self.table.noun, job.id)
        return self._out(db, job)

    def cancel(self, db: Session, job_pk: int) -> BaseModel:
        """Remove a job that is still waiting its turn. One already sent to Amazon can't be cancelled."""
        job = self._get(db, job_pk)
        if job.sync_status != QUEUED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Only queued requests can be cancelled; this one is {job.sync_status}",
            )
        self._repo.update(db, job, sync_status=CANCELLED, completed_at=now())
        return self._out(db, job)

    def schedule_periods(
        self, db: Session, job_type: str, payload: ReportScheduleIn, requested_by_id: int
    ) -> BaseModel:
        """Split the period into consecutive `partition_days`-day periods and queue one job each.

        E.g. Jan 1 - Mar 10 with 10 days: Jan 1-10, Jan 11-20, ..., Mar 2-10. Periods already queued
        or processing are skipped rather than failing the whole schedule.
        """
        queued, skipped = [], []
        for start, end in split_period(payload.start_date, payload.end_date, days=payload.partition_days):
            try:
                queued.append(
                    self.enqueue(db, job_type, payload.marketplace_id, start, end, requested_by_id=requested_by_id)
                )
            except HTTPException as exc:
                if exc.status_code != status.HTTP_409_CONFLICT:
                    raise  # e.g. marketplace not allowed: the same for every period
                skipped.append(SkippedPeriodOut(start_date=start.date(), end_date=end.date(), reason=exc.detail))
        return self.table.batch_out(queued=queued, skipped=skipped)

    # ---------- Tracking ----------

    def get(self, db: Session, job_pk: int) -> BaseModel:
        return self._out(db, self._get(db, job_pk))

    def status(self, db: Session) -> BaseModel:
        """The job being processed now and every job waiting behind it, in order."""
        active = self._repo.list_by_sync_status(db, ACTIVE)
        current = next((j for j in active if j.sync_status == PROCESSING), None)
        pending = [j for j in active if j.sync_status == QUEUED]
        job_out = self.table.job_out
        return self.table.queue_out(
            current=job_out.model_validate(current) if current else None,
            pending=[
                job_out.model_validate(j).model_copy(update={"queue_position": i})
                for i, j in enumerate(pending, start=1)
            ],
            counts={s: 0 for s in ALL_STATUSES} | self._repo.count_by_sync_status(db),
        )

    def coverage(self, db: Session, job_type: str, marketplace_id: str) -> ReportCoverageOut:
        """Days of the marketplace covered by jobs of a type, per sync status."""
        rows = self._repo.list_periods(db, job_type, marketplace_id, ALL_STATUSES)
        by_status = {
            st.lower(): _merge([(s.date(), e.date()) for s, e, row_st in rows if row_st == st]) for st in ALL_STATUSES
        }
        return ReportCoverageOut(**by_status)

    def _get(self, db: Session, job_pk: int) -> Any:
        job = self._repo.get(db, job_pk)
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{self.table.noun.capitalize()} not found")
        return job

    def _out(self, db: Session, job: Any) -> BaseModel:
        out = self.table.job_out.model_validate(job)
        if job.sync_status == QUEUED:
            position = self._repo.count_queued_before(db, QUEUED, job.id) + 1
            out = out.model_copy(update={"queue_position": position})
        return out

    # ---------- Worker ----------

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name=f"{self.table.lock_name}", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        # A job mid-way stays PROCESSING and is resumed on the next start.
        self._stop.set()
        self._wake.set()

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                with engine.connect() as lock_conn:
                    # The lock lives as long as this connection: only one process works the queue.
                    if not lock_conn.scalar(text("SELECT GET_LOCK(:name, 0)"), {"name": self.table.lock_name}):
                        self._stop.wait(POLL_SECONDS * 6)
                        continue
                    logger.info("%s queue worker is running", self.table.noun.capitalize())
                    self._resume_interrupted()
                    while not self._stop.is_set():
                        lock_conn.scalar(text("SELECT 1"))  # fail fast if the lock connection dropped
                        if not self._process_next():
                            self._wake.wait(POLL_SECONDS)
                            self._wake.clear()
            except Exception:
                logger.exception("%s queue worker error; restarting", self.table.noun.capitalize())
                self._stop.wait(POLL_SECONDS)

    def _resume_interrupted(self) -> None:
        db = SessionLocal()
        try:
            # Nothing else can be processing while we hold the lock, so these were cut off by a restart.
            count = self._repo.set_sync_status(db, [PROCESSING], QUEUED)
            if count:
                logger.warning("Resuming %d %s job(s) interrupted by a restart", count, self.table.noun)
        finally:
            db.close()

    def _process_next(self) -> bool:
        """Run the oldest queued job to completion. False if the queue is empty."""
        db = SessionLocal()
        try:
            job = self._repo.next_queued(db, QUEUED)
            if job is None:
                return False
            try:
                self._process(db, job)
            except Exception as exc:
                db.rollback()
                logger.exception("%s request %s (%s) failed", self.table.noun.capitalize(), job.id, self._type(job))
                self._repo.update(db, job, sync_status=FAILED, error=str(exc)[:5000], completed_at=now())
            return True
        finally:
            db.close()

    def _process(self, db: Session, job: Any) -> None:
        handler = self._handlers.get(self._type(job))
        if handler is None:
            raise RuntimeError(f"No JobHandler registered for {self._type(job)}")

        amazon_id = self.table.amazon_id_field
        self._repo.update(db, job, sync_status=PROCESSING, started_at=job.started_at or now())
        if getattr(job, amazon_id) is None:
            self._repo.update(
                db, job, **{amazon_id: handler.request(job)}, processing_status=ProcessingStatus.IN_QUEUE
            )

        def on_status(processing_status: str) -> None:
            if processing_status != job.processing_status:
                self._repo.update(db, job, processing_status=processing_status)

        try:
            done = handler.wait(job, on_status)
        except ReportProcessingError as exc:
            if exc.processing_status == ProcessingStatus.CANCELLED:
                # Amazon cancels a job by itself when there's no data for the range.
                self._repo.update(
                    db,
                    job,
                    processing_status=exc.processing_status,
                    sync_status=SYNCED,
                    error="Amazon returned no data for the selected date range",
                    completed_at=now(),
                )
                return
            self._repo.update(db, job, processing_status=exc.processing_status)
            raise

        # DONE while still PROCESSING = downloading and saving rows.
        self._repo.update(
            db, job, processing_status=ProcessingStatus.DONE, **{self.table.document_field: handler.document_id(done)}
        )
        row_count, inserted = handler.store(db, job, done)
        self._repo.update(
            db,
            job,
            sync_status=SYNCED,
            row_count=row_count,
            inserted_count=inserted,
            skipped_count=row_count - inserted,
            error=None,
            completed_at=now(),
        )
        logger.info(
            "Stored %s %s (%s) for %s (%s): %d rows, %d new, %d skipped",
            self.table.noun, getattr(job, amazon_id), self._type(job), job.marketplace_id, job.region,
            row_count, inserted, row_count - inserted,
        )
