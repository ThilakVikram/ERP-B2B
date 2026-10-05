from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.integration.amazon import Region
from app.schemas.report import AmazonReportOut, ReportQueueOut, ReportSyncStatus
from app.schemas.seller import MarketplaceParticipationOut
from app.services.report_queue_service import list_report_marketplaces, list_reports, report_queue

router = APIRouter(prefix="/reports", tags=["reports"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[AmazonReportOut])
def list_all_reports(
    region: Region | None = None,
    marketplace_id: str | None = Query(None, alias="marketplaceId"),
    report_types: list[str] | None = Query(None, alias="reportType"),
    sync_status: list[ReportSyncStatus] | None = Query(None, alias="status"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Latest report requests, newest first. Every filter is optional; `reportType`
    and `status` can repeat (e.g. ?status=QUEUED&status=PROCESSING)."""
    return list_reports(db, region.value if region else None, marketplace_id, report_types, sync_status, limit)


@router.get("/queue", response_model=ReportQueueOut)
def get_queue(db: Session = Depends(get_db)):
    """The report being processed now and every request waiting behind it (all report types)."""
    return report_queue.status(db)


@router.get("/marketplaces", response_model=list[MarketplaceParticipationOut])
def list_marketplaces(region: Region | None = None, db: Session = Depends(get_db)):
    """Marketplaces reports can be requested for, from the seller's marketplace participations."""
    return list_report_marketplaces(db, region.value if region else None)


@router.get("/{report_id}", response_model=AmazonReportOut)
def get_report(report_id: int, db: Session = Depends(get_db)):
    """Status of one report request (any report type)."""
    return report_queue.get(db, report_id)


@router.post("/{report_id}/cancel", response_model=AmazonReportOut)
def cancel_report(report_id: int, db: Session = Depends(get_db)):
    """Cancel a request that is still queued."""
    return report_queue.cancel(db, report_id)
