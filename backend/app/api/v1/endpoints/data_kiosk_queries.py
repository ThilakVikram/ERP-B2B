from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.integration.amazon import Region
from app.schemas.data_kiosk_query import DataKioskQueryOut, DataKioskQueueOut, DataKioskSyncStatus
from app.services.data_kiosk_queue_service import data_kiosk_queue, list_queries

# The Data Kiosk queue (amazon_intg_data_kiosk_queries), separate from the report queue (/reports).
router = APIRouter(prefix="/data-kiosk/queries", tags=["data kiosk: queue"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[DataKioskQueryOut])
def list_all_queries(
    region: Region | None = None,
    marketplace_id: str | None = Query(None, alias="marketplaceId"),
    query_types: list[str] | None = Query(None, alias="queryType"),
    sync_status: list[DataKioskSyncStatus] | None = Query(None, alias="status"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Latest Data Kiosk queries, newest first. Every filter is optional; `queryType` and `status`
    can repeat (e.g. ?status=QUEUED&status=PROCESSING)."""
    return list_queries(db, region.value if region else None, marketplace_id, query_types, sync_status, limit)


@router.get("/queue", response_model=DataKioskQueueOut)
def get_queue(db: Session = Depends(get_db)):
    """The query being processed now and every query waiting behind it (all query types)."""
    return data_kiosk_queue.status(db)


@router.get("/{query_pk}", response_model=DataKioskQueryOut)
def get_query(query_pk: int, db: Session = Depends(get_db)):
    """Status of one Data Kiosk query."""
    return data_kiosk_queue.get(db, query_pk)


@router.post("/{query_pk}/cancel", response_model=DataKioskQueryOut)
def cancel_query(query_pk: int, db: Session = Depends(get_db)):
    """Cancel a query that is still queued."""
    return data_kiosk_queue.cancel(db, query_pk)
