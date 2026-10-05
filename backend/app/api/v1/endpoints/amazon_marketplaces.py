from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.integration.amazon import Region
from app.schemas.amazon_marketplace import AmazonMarketplaceOut, AmazonMarketplaceSyncOut
from app.schemas.sync_mode import SyncMode
from app.services import amazon_marketplace_service

router = APIRouter(
    prefix="/platform/amazon/marketplaces",
    tags=["platform: amazon marketplaces"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=list[AmazonMarketplaceOut])
def list_marketplaces(region: Region | None = None, db: Session = Depends(get_db)):
    return amazon_marketplace_service.list_marketplaces(db, region)


@router.post("/sync", response_model=AmazonMarketplaceSyncOut)
def sync_marketplaces(
    region: Region | None = None, mode: SyncMode = SyncMode.NORMAL, db: Session = Depends(get_db)
):
    """Create/update marketplaces from the stored marketplace participations (all regions when none given).

    mode=normal (default) only takes rows not linked yet; mode=full refreshes every row. Nothing is deleted.
    """
    return amazon_marketplace_service.sync_from_integration(db, region, mode)
