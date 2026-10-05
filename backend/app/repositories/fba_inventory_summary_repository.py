"""Database access for the FbaInventorySummary model. No business logic here."""

from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.integration.amazon.inventory.fba_inventory_summary import FbaInventorySummary


def list_all(
    db: Session, region: str | None = None, marketplace_id: str | None = None
) -> list[FbaInventorySummary]:
    stmt = select(FbaInventorySummary).order_by(
        FbaInventorySummary.region, FbaInventorySummary.marketplace_id, FbaInventorySummary.seller_sku
    )
    if region:
        stmt = stmt.where(FbaInventorySummary.region == region)
    if marketplace_id:
        stmt = stmt.where(FbaInventorySummary.marketplace_id == marketplace_id)
    return list(db.scalars(stmt))


def replace_marketplace(db: Session, region: str, marketplace_id: str, rows: Iterable[dict]) -> int:
    """Upsert `rows` (keyed by seller_sku) for one marketplace and delete its SKUs Amazon no longer returns.

    One transaction. Returns the number of rows now stored for the marketplace.
    """
    existing = {s.seller_sku: s for s in list_all(db, region, marketplace_id)}
    seen: set[str] = set()

    for fields in rows:
        sku = fields["seller_sku"]
        seen.add(sku)
        summary = existing.get(sku)
        if summary is None:
            db.add(FbaInventorySummary(region=region, marketplace_id=marketplace_id, **fields))
        else:
            for key, value in fields.items():
                setattr(summary, key, value)

    for sku, summary in existing.items():
        if sku not in seen:
            db.delete(summary)
    db.commit()
    return len(seen)
