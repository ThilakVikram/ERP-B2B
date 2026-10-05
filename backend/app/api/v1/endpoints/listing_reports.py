from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.integration.amazon import Region
from app.models.user import User
from app.schemas.listing_report import ListingReportCreateIn, ListingsSummaryOut, MerchantListingOut
from app.schemas.report import ReportBatchOut
from app.services import listing_report_service

router = APIRouter(
    prefix="/reports/listings", tags=["reports: listings"], dependencies=[Depends(get_current_user)]
)


@router.post("/all-listings", response_model=ReportBatchOut, status_code=status.HTTP_202_ACCEPTED)
def create_all_listings_reports(
    payload: ListingReportCreateIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Queue a GET_MERCHANT_LISTINGS_ALL_DATA snapshot for each marketplace.

    Marketplaces with a snapshot already queued or processing today come back under `skipped`.
    """
    return listing_report_service.request_reports(db, payload, requested_by_id=user.id)


@router.get("/summary", response_model=list[ListingsSummaryOut])
def summarize_listings(db: Session = Depends(get_db)):
    """Stored listings per region and marketplace."""
    return listing_report_service.summarize_listings(db)


@router.get("/items", response_model=list[MerchantListingOut])
def list_listings(
    region: Region | None = None,
    marketplace_id: str | None = Query(None, alias="marketplaceId"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return listing_report_service.list_listings(db, region, marketplace_id, limit, offset)
