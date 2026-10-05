"""Database access for the AmazonMarketplace model. No business logic here."""

from collections.abc import Iterable

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.amazon.marketplace import AmazonMarketplace
from app.models.integration.amazon.sellers.marketplace_participation import MarketplaceParticipation


def list_all(db: Session, region: str | None = None) -> list[AmazonMarketplace]:
    stmt = select(AmazonMarketplace).order_by(AmazonMarketplace.region, AmazonMarketplace.country_code)
    if region:
        stmt = stmt.where(AmazonMarketplace.region == region)
    return list(db.scalars(stmt))


def upsert_all(db: Session, rows: Iterable[dict]) -> int:
    """Create marketplaces not stored yet and update stored ones, matched on Amazon's marketplace_id.
    One transaction. Returns the number created."""
    rows = list(rows)
    existing = {
        m.marketplace_id: m
        for m in db.scalars(
            select(AmazonMarketplace).where(AmazonMarketplace.marketplace_id.in_([r["marketplace_id"] for r in rows]))
        )
    }
    created = 0
    for fields in rows:
        marketplace = existing.get(fields["marketplace_id"])
        if marketplace is None:
            db.add(AmazonMarketplace(**fields))
            created += 1
        else:
            for key, value in fields.items():
                setattr(marketplace, key, value)
    db.flush()
    # The other direction: each participation points at the marketplace created from it.
    db.execute(
        update(MarketplaceParticipation)
        .where(MarketplaceParticipation.id == AmazonMarketplace.integration_id)
        # Keep updated_at: it tracks the Sellers API sync, not this link.
        .values(amazon_marketplace_id=AmazonMarketplace.id, updated_at=MarketplaceParticipation.updated_at)
    )
    db.commit()
    return created
