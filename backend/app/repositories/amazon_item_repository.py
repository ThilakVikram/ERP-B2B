"""Database access for the AmazonItem model. No business logic here."""

from sqlalchemy import Select, func, or_, select, update
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import Session, joinedload

from app.models.amazon.item import AmazonItem
from app.models.amazon.marketplace import AmazonMarketplace
from app.models.integration.amazon.reports.listing.merchant_listing import MerchantListing

# Item columns filled from the merchant listing (and its marketplace), in insert order.
_FROM_LISTING = [
    "amazon_marketplace_id",
    "integration_id",
    "seller_sku",
    "asin",
    "title",
    "item_condition",
    "fulfillment_channel",
    "price",
    "currency_code",
    "image_url",
    "status",
]
# Updated on every sync; the key columns are not.
_UPDATED = [c for c in _FROM_LISTING if c not in {"amazon_marketplace_id", "seller_sku"}]


def _filtered(stmt: Select, region: str | None, amazon_marketplace_id: int | None, q: str | None) -> Select:
    if region:
        stmt = stmt.where(AmazonMarketplace.region == region)
    if amazon_marketplace_id:
        stmt = stmt.where(AmazonItem.amazon_marketplace_id == amazon_marketplace_id)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(AmazonItem.seller_sku.like(like), AmazonItem.asin.like(like), AmazonItem.title.like(like)))
    return stmt


def list_page(
    db: Session,
    region: str | None = None,
    amazon_marketplace_id: int | None = None,
    q: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[int, list[AmazonItem]]:
    """One page of items (with their marketplace) and the total matching the filters."""
    base = select(AmazonItem).join(AmazonItem.marketplace)
    total = db.scalar(
        _filtered(select(func.count()).select_from(AmazonItem).join(AmazonItem.marketplace), region, amazon_marketplace_id, q)
    )
    stmt = (
        _filtered(base, region, amazon_marketplace_id, q)
        .options(joinedload(AmazonItem.marketplace))
        .order_by(AmazonMarketplace.region, AmazonMarketplace.country_code, AmazonItem.seller_sku)
        .limit(limit)
        .offset(offset)
    )
    return total or 0, list(db.scalars(stmt))


def _count_items(db: Session, region: str | None) -> int:
    stmt = select(func.count()).select_from(AmazonItem).join(AmazonItem.marketplace)
    if region:
        stmt = stmt.where(AmazonMarketplace.region == region)
    return db.scalar(stmt) or 0


def upsert_from_merchant_listings(
    db: Session, region: str | None = None, only_unlinked: bool = False
) -> tuple[int, int, int]:
    """Create/update items from amazon_intg_merchant_listings in one INSERT ... SELECT ... ON DUPLICATE KEY
    UPDATE, matching each listing to its amazon_marketplaces row by Amazon's marketplace_id. One transaction.
    only_unlinked: only listings whose amazon_item_id is null.

    Returns (created, updated, skipped); skipped = listings whose marketplace has no amazon_marketplaces row.
    """
    source = select(
        AmazonMarketplace.id,
        MerchantListing.id,
        MerchantListing.seller_sku,
        MerchantListing.asin,
        MerchantListing.item_name,
        MerchantListing.item_condition,
        MerchantListing.fulfillment_channel,
        MerchantListing.price,
        AmazonMarketplace.currency_code,
        MerchantListing.image_url,
        MerchantListing.status,
    ).join(AmazonMarketplace, AmazonMarketplace.marketplace_id == MerchantListing.marketplace_id)
    listings = select(func.count()).select_from(MerchantListing)
    if region:
        source = source.where(MerchantListing.region == region)
        listings = listings.where(MerchantListing.region == region)
    if only_unlinked:
        source = source.where(MerchantListing.amazon_item_id.is_(None))
        listings = listings.where(MerchantListing.amazon_item_id.is_(None))

    matched = db.scalar(select(func.count()).select_from(source.subquery())) or 0
    total_listings = db.scalar(listings) or 0
    before = _count_items(db, region)

    stmt = insert(AmazonItem).from_select(_FROM_LISTING, source)
    db.execute(stmt.on_duplicate_key_update({c: stmt.inserted[c] for c in _UPDATED} | {"updated_at": func.now()}))
    # The other direction: each listing points at the item created from it (one UPDATE ... JOIN).
    link = (
        update(MerchantListing)
        .where(MerchantListing.id == AmazonItem.integration_id)
        # Keep updated_at: it tracks the report's changes, not this link.
        .values(amazon_item_id=AmazonItem.id, updated_at=MerchantListing.updated_at)
    )
    if region:
        link = link.where(MerchantListing.region == region)
    if only_unlinked:
        link = link.where(MerchantListing.amazon_item_id.is_(None))
    db.execute(link)
    db.commit()

    created = _count_items(db, region) - before
    return created, matched - created, total_listings - matched
