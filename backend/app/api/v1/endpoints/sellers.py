from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.integration.amazon import Region
from app.schemas.seller import MarketplaceParticipationOut, MarketplaceParticipationSyncOut
from app.services import seller_service

router = APIRouter(
    prefix="/sellers", tags=["sellers"], dependencies=[Depends(get_current_user)]
)


@router.post("/{region}/sync", response_model=MarketplaceParticipationSyncOut)
def sync_marketplace_participations(region: Region, db: Session = Depends(get_db)):
    return seller_service.sync_region(db, region)


@router.get("/marketplace-participations", response_model=list[MarketplaceParticipationOut])
def list_marketplace_participations(region: Region | None = None, db: Session = Depends(get_db)):
    return seller_service.list_participations(db, region)
