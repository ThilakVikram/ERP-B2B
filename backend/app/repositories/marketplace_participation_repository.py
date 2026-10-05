"""Database access for the MarketplaceParticipation model. No business logic here."""

from collections.abc import Iterable

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.integration.amazon.sellers.marketplace_participation import MarketplaceParticipation


def list_all(db: Session, region: str | None = None) -> list[MarketplaceParticipation]:
    stmt = select(MarketplaceParticipation).order_by(
        MarketplaceParticipation.region, MarketplaceParticipation.country_code
    )
    if region:
        stmt = stmt.where(MarketplaceParticipation.region == region)
    return list(db.scalars(stmt))


def replace_region(db: Session, region: str, rows: Iterable[dict]) -> list[MarketplaceParticipation]:
    """Upsert `rows` for `region` and delete that region's rows Amazon no longer returns. One transaction."""
    existing = {p.marketplace_id: p for p in list_all(db, region)}
    rows = list(rows)

    for fields in rows:
        participation = existing.get(fields["marketplace_id"])
        if participation is None:
            db.add(MarketplaceParticipation(region=region, **fields))
        else:
            for key, value in fields.items():
                setattr(participation, key, value)

    returned_ids = [fields["marketplace_id"] for fields in rows]
    db.execute(
        delete(MarketplaceParticipation).where(
            MarketplaceParticipation.region == region,
            MarketplaceParticipation.marketplace_id.not_in(returned_ids),
        )
    )
    db.commit()
    return list_all(db, region)


def list_participating(db: Session, region: str | None = None) -> list[MarketplaceParticipation]:
    stmt = select(MarketplaceParticipation).where(MarketplaceParticipation.is_participating.is_(True)).order_by(
        MarketplaceParticipation.region, MarketplaceParticipation.country_code, MarketplaceParticipation.name
    )
    if region:
        stmt = stmt.where(MarketplaceParticipation.region == region)
    return list(db.scalars(stmt))


def get_participating(db: Session, marketplace_id: str) -> MarketplaceParticipation | None:
    stmt = select(MarketplaceParticipation).where(
        MarketplaceParticipation.marketplace_id == marketplace_id,
        MarketplaceParticipation.is_participating.is_(True),
    )
    return db.scalars(stmt).first()
