"""App marketplaces (amazon_marketplaces), created/updated from the integration's marketplace participations."""

from sqlalchemy.orm import Session

from app.integration.amazon import Region
from app.repositories import amazon_marketplace_repository, marketplace_participation_repository
from app.schemas.amazon_marketplace import AmazonMarketplaceOut, AmazonMarketplaceSyncOut
from app.schemas.sync_mode import SyncMode


def sync_from_integration(
    db: Session, region: Region | None = None, mode: SyncMode = SyncMode.NORMAL
) -> AmazonMarketplaceSyncOut:
    """Create/update marketplaces from the stored marketplace participations (of `region`, or all).

    normal: only participations not linked to a marketplace yet (amazon_marketplace_id is null).
    full: every participation, refreshing marketplaces already created. Nothing is deleted.
    Only reads the database; it does not call Amazon.
    """
    participations = marketplace_participation_repository.list_all(db, region.value if region else None)
    if mode is SyncMode.NORMAL:
        participations = [p for p in participations if p.amazon_marketplace_id is None]
    rows = [
        {
            "integration_id": p.id,
            "region": p.region,
            "marketplace_id": p.marketplace_id,
            "name": p.name,
            "country_code": p.country_code,
            "currency_code": p.default_currency_code,
            "language_code": p.default_language_code,
            "domain_name": p.domain_name,
            "store_name": p.store_name,
            "is_active": p.is_participating,
        }
        for p in participations
    ]
    created = amazon_marketplace_repository.upsert_all(db, rows)
    return AmazonMarketplaceSyncOut(
        mode=mode,
        created=created,
        updated=len(rows) - created,
        marketplaces=list_marketplaces(db, region),
    )


def list_marketplaces(db: Session, region: Region | None = None) -> list[AmazonMarketplaceOut]:
    rows = amazon_marketplace_repository.list_all(db, region.value if region else None)
    return [AmazonMarketplaceOut.model_validate(m) for m in rows]
