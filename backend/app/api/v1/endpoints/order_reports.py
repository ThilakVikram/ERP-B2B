from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.integration.amazon import Region
from app.models.user import User
from app.schemas.order_report import (
    OrderReportCreateIn,
    OrderReportItemOut,
    OrderItemsSummaryOut,
)
from app.schemas.report import AmazonReportOut, ReportBatchOut, ReportCoverageOut, ReportScheduleIn
from app.services import order_report_service

router = APIRouter(
    prefix="/reports/orders", tags=["reports: orders"], dependencies=[Depends(get_current_user)]
)


@router.post(
    "/all-orders-by-order-date",
    response_model=AmazonReportOut,
    status_code=status.HTTP_202_ACCEPTED,
    responses={409: {"description": "The same report is already queued or processing"}},
)
def create_all_orders_by_order_date_report(
    payload: OrderReportCreateIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Queue GET_FLAT_FILE_ALL_ORDERS_DATA_BY_ORDER_DATE_GENERAL for orders placed in the period.

    Reports run one at a time; track it with GET /reports/queue or GET /reports/{id}.
    """
    return order_report_service.request_report(db, payload, requested_by_id=user.id)


@router.post(
    "/all-orders-by-order-date/schedule",
    response_model=ReportBatchOut,
    status_code=status.HTTP_202_ACCEPTED,
)
def schedule_all_orders_by_order_date_reports(
    payload: ReportScheduleIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Queue GET_FLAT_FILE_ALL_ORDERS_DATA_BY_ORDER_DATE_GENERAL for the period, split into
    consecutive reports of `partitionDays` days (1-30). Periods already queued or processing
    come back under `skipped`.
    """
    return order_report_service.schedule_reports(db, payload, requested_by_id=user.id)


@router.get("/all-orders-by-order-date", response_model=list[AmazonReportOut])
def list_all_orders_by_order_date_reports(
    region: Region | None = None,
    marketplace_id: str | None = Query(None, alias="marketplaceId"),
    db: Session = Depends(get_db),
):
    return order_report_service.list_reports(db, region, marketplace_id)


@router.get("/all-orders-by-order-date/coverage", response_model=ReportCoverageOut)
def get_all_orders_by_order_date_coverage(
    marketplace_id: str = Query(alias="marketplaceId"), db: Session = Depends(get_db)
):
    """Days of the marketplace already in the queue or already fetched, as merged periods."""
    return order_report_service.get_coverage(db, marketplace_id)


@router.get("/items/summary", response_model=list[OrderItemsSummaryOut])
def summarize_order_items(db: Session = Depends(get_db)):
    """Stored order item rows per region and marketplace."""
    return order_report_service.summarize_order_items(db)


@router.get("/items", response_model=list[OrderReportItemOut])
def list_order_items(
    region: Region | None = None,
    marketplace_id: str | None = Query(None, alias="marketplaceId"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return order_report_service.list_order_items(db, region, marketplace_id, limit, offset)
