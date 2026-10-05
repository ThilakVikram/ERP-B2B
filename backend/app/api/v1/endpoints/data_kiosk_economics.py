from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.integration.amazon import Region
from app.models.user import User
from app.schemas.data_kiosk_economics import SkuEconomicsOut, SkuEconomicsSummaryOut
from app.schemas.data_kiosk_query import DataKioskBatchOut
from app.schemas.report import ReportCoverageOut, ReportScheduleIn
from app.services import data_kiosk_economics_service

# Queue status, history and cancelling: /data-kiosk/queries (endpoints/data_kiosk_queries.py).
router = APIRouter(
    prefix="/data-kiosk/economics", tags=["data kiosk: economics"], dependencies=[Depends(get_current_user)]
)


@router.post(
    "/sku-economics/schedule",
    response_model=DataKioskBatchOut,
    status_code=status.HTTP_202_ACCEPTED,
)
def schedule_sku_economics(
    payload: ReportScheduleIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Queue the SKU Economics query for the period, split into consecutive queries of
    `partitionDays` days (1-30). Periods already queued or processing come back under `skipped`.
    """
    return data_kiosk_economics_service.schedule_queries(db, payload, requested_by_id=user.id)


@router.get("/sku-economics/coverage", response_model=ReportCoverageOut)
def get_sku_economics_coverage(marketplace_id: str = Query(alias="marketplaceId"), db: Session = Depends(get_db)):
    """Days of the marketplace already in the queue or already fetched, as merged periods."""
    return data_kiosk_economics_service.get_coverage(db, marketplace_id)


@router.get("/sku-economics/summary", response_model=list[SkuEconomicsSummaryOut])
def summarize_sku_economics(db: Session = Depends(get_db)):
    """Stored SKU economics per region and marketplace."""
    return data_kiosk_economics_service.summarize(db)


@router.get("/sku-economics", response_model=list[SkuEconomicsOut])
def list_sku_economics(
    region: Region | None = None,
    marketplace_id: str | None = Query(None, alias="marketplaceId"),
    start_date: date | None = Query(None, alias="startDate"),
    end_date: date | None = Query(None, alias="endDate"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Stored rows whose period lies within [startDate, endDate], newest period first."""
    return data_kiosk_economics_service.list_rows(db, region, marketplace_id, start_date, end_date, limit, offset)
