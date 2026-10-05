"""Database access for the MerchantListing model. No business logic here."""

from sqlalchemy import case, func, select
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import Session

from app.models.integration.amazon.reports.listing.merchant_listing import MerchantListing

CHUNK_SIZE = 1000  # rows per INSERT statement

# Updated from the report on every snapshot; the key columns, created_at and the link to the app item
# (set by the item sync, not the report) are not.
_UPDATED_COLUMNS = [
    c.name
    for c in MerchantListing.__table__.columns
    if c.name not in {"id", "region", "marketplace_id", "seller_sku", "amazon_item_id", "created_at", "updated_at"}
]


def list_all(
    db: Session,
    region: str | None = None,
    marketplace_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[MerchantListing]:
    stmt = (
        select(MerchantListing)
        .order_by(MerchantListing.region, MerchantListing.marketplace_id, MerchantListing.seller_sku)
        .limit(limit)
        .offset(offset)
    )
    if region:
        stmt = stmt.where(MerchantListing.region == region)
    if marketplace_id:
        stmt = stmt.where(MerchantListing.marketplace_id == marketplace_id)
    return list(db.scalars(stmt))


def upsert_all(db: Session, region: str, marketplace_id: str, amazon_report_id: int, rows: list[dict]) -> int:
    """Bulk upsert listings, CHUNK_SIZE per multi-row INSERT ... ON DUPLICATE KEY UPDATE. One transaction.

    New SKUs are inserted; SKUs already stored for the marketplace get the report's values.
    Values are sent as bound parameters (never formatted into the SQL). Returns the number of new SKUs.
    """
    fixed = {"region": region, "marketplace_id": marketplace_id, "amazon_report_id": amazon_report_id}
    # A report can list a SKU twice; the last row wins, as it would with sequential upserts.
    by_sku = {fields["seller_sku"]: {**fields, **fixed} for fields in rows}
    rows = list(by_sku.values())
    inserted = 0
    for start in range(0, len(rows), CHUNK_SIZE):
        chunk = rows[start : start + CHUNK_SIZE]
        # The driver reports updated and unchanged rows alike (FOUND_ROWS), so count new SKUs up front.
        existing = db.scalar(
            select(func.count()).where(
                MerchantListing.region == region,
                MerchantListing.marketplace_id == marketplace_id,
                MerchantListing.seller_sku.in_([r["seller_sku"] for r in chunk]),
            )
        )
        stmt = insert(MerchantListing).values(chunk)
        db.execute(
            stmt.on_duplicate_key_update(
                {name: stmt.inserted[name] for name in _UPDATED_COLUMNS} | {"updated_at": func.now()}
            )
        )
        inserted += len(chunk) - existing
    db.commit()
    return inserted


def summary_by_marketplace(db: Session) -> list[dict]:
    """Listing counts, units and last update per (region, marketplace)."""
    stmt = (
        select(
            MerchantListing.region,
            MerchantListing.marketplace_id,
            func.count().label("listing_count"),
            func.sum(case((MerchantListing.status == "Active", 1), else_=0)).label("active_count"),
            func.coalesce(func.sum(MerchantListing.quantity), 0).label("total_quantity"),
            func.max(MerchantListing.updated_at).label("last_updated_at"),
        )
        .group_by(MerchantListing.region, MerchantListing.marketplace_id)
        .order_by(MerchantListing.region, MerchantListing.marketplace_id)
    )
    return [dict(row._mapping) for row in db.execute(stmt)]
