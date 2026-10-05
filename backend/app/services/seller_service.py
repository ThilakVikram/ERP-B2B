"""Syncs Sellers API v1 marketplace participations into the database, per region."""

import logging
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.integration.amazon import AmazonApiError, AmazonConfigError, AmazonCredentials, Region
from app.integration.amazon.sellers import SellersService
from app.repositories import marketplace_participation_repository
from app.schemas.seller import MarketplaceParticipationOut, MarketplaceParticipationSyncOut

logger = logging.getLogger(__name__)


def sync_region(db: Session, region: Region) -> MarketplaceParticipationSyncOut:
    """Fetch the region's marketplace participations from Amazon and replace that region's rows."""
    try:
        participations = SellersService(AmazonCredentials.from_env(region)).get_marketplace_participations()
    except AmazonConfigError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except AmazonApiError as exc:
        logger.error("Sellers API sync for %s failed: %s", region.value, exc)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    synced_at = datetime.now(timezone.utc).replace(tzinfo=None)
    rows = [
        {
            "marketplace_id": p.marketplace.id,
            "name": p.marketplace.name,
            "country_code": p.marketplace.country_code,
            "default_currency_code": p.marketplace.default_currency_code,
            "default_language_code": p.marketplace.default_language_code,
            "domain_name": p.marketplace.domain_name,
            "store_name": p.store_name,
            "is_participating": bool(p.participation.is_participating),
            "has_suspended_listings": bool(p.participation.has_suspended_listings),
            "last_synced_at": synced_at,
        }
        for p in participations
    ]
    saved = marketplace_participation_repository.replace_region(db, region.value, rows)
    logger.info("Synced %d marketplace participations for %s", len(saved), region.value)
    return MarketplaceParticipationSyncOut(
        region=region,
        count=len(saved),
        participations=[MarketplaceParticipationOut.model_validate(p) for p in saved],
    )


def list_participations(db: Session, region: Region | None = None) -> list[MarketplaceParticipationOut]:
    rows = marketplace_participation_repository.list_all(db, region.value if region else None)
    return [MarketplaceParticipationOut.model_validate(p) for p in rows]
