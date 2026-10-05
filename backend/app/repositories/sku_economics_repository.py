"""Database access for the SkuEconomics model. No business logic here."""

from datetime import date

from sqlalchemy import delete, func, insert, select, tuple_
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.orm import Session

from app.models.integration.amazon.data_kiosk.economics.sku_economics import SkuEconomics, SkuEconomicsAd, SkuEconomicsCost, SkuEconomicsFee

CHUNK_SIZE = 1000  # rows per INSERT statement

_KEY = ("marketplace_id", "msku", "fnsku", "start_date", "end_date")
# Breakdown rows per SKU period: key in the row dict -> table.
_CHILDREN = {"fees": SkuEconomicsFee, "ads": SkuEconomicsAd, "costs": SkuEconomicsCost}
# Updated from the query on every run; the key columns and created_at are not.
_UPDATED_COLUMNS = [
    c.name
    for c in SkuEconomics.__table__.columns
    if c.name not in {"id", *_KEY, "created_at", "updated_at"}
]


def upsert_all(db: Session, region: str, data_kiosk_query_id: int, rows: list[dict]) -> int:
    """Bulk upsert rows with their fee / ad / cost breakdowns, CHUNK_SIZE SKU periods at a time.
    One transaction.

    `rows` are SkuEconomicsRow dicts; their "fees", "ads" and "costs" lists go to their own tables.
    New (marketplace, SKU, FNSKU, period) rows are inserted; stored ones get the new values and their
    breakdown rows are replaced. Values are sent as bound parameters (never formatted into the SQL).
    Returns the number of new SKU periods.
    """
    fixed = {"region": region, "data_kiosk_query_id": data_kiosk_query_id}
    # The last record wins if a key repeats, as it would with sequential upserts.
    rows = list({tuple(r[k] for k in _KEY): {**r, **fixed} for r in rows}.values())
    key = tuple_(*(getattr(SkuEconomics, k) for k in _KEY))
    inserted = 0
    for start in range(0, len(rows), CHUNK_SIZE):
        chunk = rows[start : start + CHUNK_SIZE]
        keys = [tuple(r[k] for k in _KEY) for r in chunk]
        parents = [{k: v for k, v in r.items() if k not in _CHILDREN} for r in chunk]

        # The driver reports updated and unchanged rows alike (FOUND_ROWS), so count new keys up front.
        existing = db.scalar(select(func.count()).where(key.in_(keys)))
        stmt = mysql_insert(SkuEconomics).values(parents)
        db.execute(
            stmt.on_duplicate_key_update(
                {name: stmt.inserted[name] for name in _UPDATED_COLUMNS} | {"updated_at": func.now()}
            )
        )
        inserted += len(chunk) - existing

        # Replace the breakdown rows of every SKU period in the chunk.
        ids = {tuple(row[:-1]): row[-1] for row in db.execute(select(*key.clauses, SkuEconomics.id).where(key.in_(keys)))}
        for name, model in _CHILDREN.items():
            db.execute(delete(model).where(model.sku_economics_id.in_(ids.values())))
            children = [{**child, "sku_economics_id": ids[k]} for k, r in zip(keys, chunk) for child in r[name]]
            for i in range(0, len(children), CHUNK_SIZE):
                db.execute(insert(model), children[i : i + CHUNK_SIZE])
    db.commit()
    return inserted


def list_all(
    db: Session,
    region: str | None = None,
    marketplace_id: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[SkuEconomics]:
    """Rows whose period lies within [start_date, end_date], newest period first."""
    stmt = (
        select(SkuEconomics)
        .order_by(SkuEconomics.start_date.desc(), SkuEconomics.net_product_sales.desc(), SkuEconomics.id)
        .limit(limit)
        .offset(offset)
    )
    if region:
        stmt = stmt.where(SkuEconomics.region == region)
    if marketplace_id:
        stmt = stmt.where(SkuEconomics.marketplace_id == marketplace_id)
    if start_date:
        stmt = stmt.where(SkuEconomics.start_date >= start_date)
    if end_date:
        stmt = stmt.where(SkuEconomics.end_date <= end_date)
    return list(db.scalars(stmt))


def summary_by_marketplace(db: Session) -> list[dict]:
    """Row count, SKUs, period span, totals and last update per (region, marketplace)."""
    stmt = (
        select(
            SkuEconomics.region,
            SkuEconomics.marketplace_id,
            func.count().label("row_count"),
            func.count(func.distinct(SkuEconomics.msku)).label("sku_count"),
            func.min(SkuEconomics.start_date).label("first_date"),
            func.max(SkuEconomics.end_date).label("last_date"),
            func.max(SkuEconomics.currency_code).label("currency_code"),
            func.coalesce(func.sum(SkuEconomics.net_units_sold), 0).label("net_units_sold"),
            func.coalesce(func.sum(SkuEconomics.net_product_sales), 0).label("net_product_sales"),
            func.coalesce(func.sum(SkuEconomics.net_proceeds_total), 0).label("net_proceeds_total"),
            func.max(SkuEconomics.updated_at).label("last_updated_at"),
        )
        .group_by(SkuEconomics.region, SkuEconomics.marketplace_id)
        .order_by(SkuEconomics.region, SkuEconomics.marketplace_id)
    )
    return [dict(row._mapping) for row in db.execute(stmt)]
