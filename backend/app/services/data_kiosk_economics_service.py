"""Data Kiosk SKU Economics (analytics_economics_2024_03_15): sales, fees, ad spend and net
proceeds per SKU for a period.

Queries go through the Data Kiosk queue (data_kiosk_queue_service, table
amazon_intg_data_kiosk_queries), which runs one query at a time independently of the report queue.
A date range is scheduled as consecutive periods of 1-30 days, one query each. Rows are bulk
upserted into amazon_intg_sku_economics in chunks: a later query for the same SKU and period
updates it (Amazon revises fees and sales).
"""

from collections.abc import Callable
from dataclasses import asdict
from datetime import date

from spapi.models.datakiosk_v2023_11_15 import Query
from sqlalchemy.orm import Session

from app.integration.amazon import AmazonCredentials, Region
from app.integration.amazon.data_kiosk.economics import SkuEconomicsQuery
from app.models.integration.amazon.data_kiosk.data_kiosk_query import DataKioskQuery
from app.repositories import sku_economics_repository
from app.schemas.data_kiosk_economics import SkuEconomicsOut, SkuEconomicsSummaryOut
from app.schemas.data_kiosk_query import DataKioskBatchOut
from app.schemas.report import ReportCoverageOut, ReportScheduleIn
from app.services.data_kiosk_queue_service import DataKioskHandler, data_kiosk_queue
from app.services.job_queue_service import get_marketplace

QUERY_TYPE = SkuEconomicsQuery.QUERY_TYPE.value


def _client(query: DataKioskQuery) -> SkuEconomicsQuery:
    return SkuEconomicsQuery(AmazonCredentials.for_marketplace(get_marketplace(query.marketplace_id)))


class SkuEconomicsHandler(DataKioskHandler):
    """Queue steps for one SKU Economics query."""

    query_type = QUERY_TYPE

    def request(self, query: DataKioskQuery) -> str:
        return _client(query).request(
            query.data_start_time.date(), query.data_end_time.date(), [query.marketplace_id]
        )

    def wait(self, query: DataKioskQuery, on_status: Callable[[str], None]) -> Query:
        return _client(query).wait(query.query_id, on_status=on_status)

    def store(self, db: Session, query: DataKioskQuery, done: Query) -> tuple[int, int]:
        # Follows every result page; each further page is another query (Amazon allows ~1 per minute).
        rows = [asdict(row) for row in _client(query).download_rows(done)]
        inserted = sku_economics_repository.upsert_all(db, query.region, query.id, rows)
        # skipped_count on the queue row = SKU periods that were already stored and got updated.
        return len(rows), inserted


data_kiosk_queue.register(SkuEconomicsHandler())


def schedule_queries(db: Session, payload: ReportScheduleIn, requested_by_id: int) -> DataKioskBatchOut:
    """Queue the period as consecutive queries of `partition_days` days (see JobQueue.schedule_periods)."""
    return data_kiosk_queue.schedule_periods(db, QUERY_TYPE, payload, requested_by_id)


def get_coverage(db: Session, marketplace_id: str) -> ReportCoverageOut:
    """Days of the marketplace already in the queue or already fetched."""
    return data_kiosk_queue.coverage(db, QUERY_TYPE, marketplace_id)


# ---------- Reads ----------


def summarize(db: Session) -> list[SkuEconomicsSummaryOut]:
    return [SkuEconomicsSummaryOut(**row) for row in sku_economics_repository.summary_by_marketplace(db)]


def list_rows(
    db: Session,
    region: Region | None = None,
    marketplace_id: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[SkuEconomicsOut]:
    rows = sku_economics_repository.list_all(
        db, region.value if region else None, marketplace_id, start_date, end_date, limit, offset
    )
    return [SkuEconomicsOut.model_validate(r) for r in rows]
