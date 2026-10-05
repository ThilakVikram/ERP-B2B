from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.integration.amazon import Region
from app.schemas.amazon_item import AmazonItemPageOut, AmazonItemSyncOut
from app.schemas.sync_mode import SyncMode
from app.services import amazon_item_service

router = APIRouter(
    prefix="/platform/amazon/items",
    tags=["platform: amazon items"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=AmazonItemPageOut)
def list_items(
    region: Region | None = None,
    amazon_marketplace_id: int | None = Query(None, alias="amazonMarketplaceId"),
    q: str | None = Query(None, max_length=100),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return amazon_item_service.list_items(db, region, amazon_marketplace_id, q, limit, offset)


@router.post("/sync", response_model=AmazonItemSyncOut)
def sync_items(
    region: Region | None = None, mode: SyncMode = SyncMode.NORMAL, db: Session = Depends(get_db)
):
    """Create/update items from the stored merchant listings (all regions when none given).

    mode=normal (default) only takes rows not linked yet; mode=full refreshes every row. Nothing is deleted.
    """
    return amazon_item_service.sync_from_integration(db, region, mode)
