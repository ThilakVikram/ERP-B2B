"""App items (amazon_items), created/updated from the integration's merchant listings."""

from sqlalchemy.orm import Session

from app.integration.amazon import Region
from app.repositories import amazon_item_repository
from app.schemas.amazon_item import AmazonItemOut, AmazonItemPageOut, AmazonItemSyncOut
from app.schemas.sync_mode import SyncMode


def sync_from_integration(
    db: Session, region: Region | None = None, mode: SyncMode = SyncMode.NORMAL
) -> AmazonItemSyncOut:
    """Create/update items from the stored merchant listings (of `region`, or all) whose marketplace exists
    in amazon_marketplaces.

    normal: only listings not linked to an item yet (amazon_item_id is null).
    full: every listing, refreshing items already created. Nothing is deleted.
    Only reads the database; it does not call Amazon.
    """
    created, updated, skipped = amazon_item_repository.upsert_from_merchant_listings(
        db, region.value if region else None, only_unlinked=mode is SyncMode.NORMAL
    )
    return AmazonItemSyncOut(mode=mode, created=created, updated=updated, skipped=skipped)


def list_items(
    db: Session,
    region: Region | None = None,
    amazon_marketplace_id: int | None = None,
    q: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> AmazonItemPageOut:
    total, rows = amazon_item_repository.list_page(
        db, region.value if region else None, amazon_marketplace_id, q, limit, offset
    )
    return AmazonItemPageOut(total=total, items=[AmazonItemOut.model_validate(r) for r in rows])
