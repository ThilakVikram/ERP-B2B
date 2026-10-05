from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.integration.amazon import Region
from app.schemas.inventory import FbaInventorySummaryOut, FbaInventorySyncOut
from app.services import inventory_service

router = APIRouter(
    prefix="/inventory", tags=["inventory"], dependencies=[Depends(get_current_user)]
)


@router.post("/{marketplace_id}/sync", response_model=FbaInventorySyncOut)
def sync_inventory_summaries(marketplace_id: str, db: Session = Depends(get_db)):
    return inventory_service.sync_marketplace(db, marketplace_id)


@router.get("/summaries", response_model=list[FbaInventorySummaryOut])
def list_inventory_summaries(
    region: Region | None = None,
    marketplace_id: str | None = Query(None, alias="marketplaceId"),
    db: Session = Depends(get_db),
):
    return inventory_service.list_summaries(db, region, marketplace_id)
