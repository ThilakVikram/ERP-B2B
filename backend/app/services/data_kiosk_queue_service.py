"""Queue for every Data Kiosk query (Data Kiosk API 2023-11-15): one query at a time, end to end.

A JobQueue (job_queue_service) over its own table, amazon_intg_data_kiosk_queries, with its own
worker: Data Kiosk has its own Amazon rate limits, so queries don't wait behind reports. Each
dataset service (e.g. data_kiosk_economics_service) registers a DataKioskHandler for its query type.

Statuses (amazon_intg_data_kiosk_queries.sync_status): QUEUED -> PROCESSING -> SYNCED | FAILED, or
CANCELLED while still QUEUED.
"""

from spapi.models.datakiosk_v2023_11_15 import Query
from sqlalchemy.orm import Session

from app.repositories import data_kiosk_query_repository
from app.schemas.data_kiosk_query import DataKioskBatchOut, DataKioskQueryOut, DataKioskQueueOut
from app.services.job_queue_service import JobHandler, JobQueue, JobTable

data_kiosk_queue = JobQueue(
    JobTable(
        repository=data_kiosk_query_repository,
        type_field="query_type",
        amazon_id_field="query_id",
        document_field="data_document_id",
        noun="Data Kiosk query",
        lock_name="itrend_data_kiosk_queue_worker",
        job_out=DataKioskQueryOut,
        queue_out=DataKioskQueueOut,
        batch_out=DataKioskBatchOut,
    )
)


class DataKioskHandler(JobHandler):
    """The query-type specific steps; `query_type` is the query type it handles."""

    query_type: str

    @property
    def job_type(self) -> str:
        return self.query_type

    def document_id(self, done: Query) -> str | None:
        # Absent when the query found no data (the first page's document if there are several).
        return done.data_document_id


def list_queries(
    db: Session,
    region: str | None = None,
    marketplace_id: str | None = None,
    query_types: list[str] | None = None,
    sync_statuses: list[str] | None = None,
    limit: int = 100,
) -> list[DataKioskQueryOut]:
    rows = data_kiosk_query_repository.list_all(db, region, marketplace_id, query_types, limit, sync_statuses)
    return [DataKioskQueryOut.model_validate(r) for r in rows]
