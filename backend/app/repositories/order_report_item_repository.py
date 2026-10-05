"""Database access for the OrderReportItem model. No business logic here."""

from sqlalchemy import func, select
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import Session

from app.models.integration.amazon.reports.order.order_report_item import OrderReportItem

CHUNK_SIZE = 1000  # rows per INSERT statement


def list_all(
    db: Session,
    region: str | None = None,
    marketplace_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[OrderReportItem]:
    stmt = (
        select(OrderReportItem)
        .order_by(OrderReportItem.purchase_date.desc(), OrderReportItem.id.desc())
        .limit(limit)
        .offset(offset)
    )
    if region:
        stmt = stmt.where(OrderReportItem.region == region)
    if marketplace_id:
        stmt = stmt.where(OrderReportItem.marketplace_id == marketplace_id)
    return list(db.scalars(stmt))


def insert_new(db: Session, region: str, marketplace_id: str, amazon_report_id: int, rows: list[dict]) -> int:
    """Bulk insert rows, CHUNK_SIZE per multi-row INSERT, skipping order items already stored. One transaction.

    Values are sent as bound parameters (never formatted into the SQL). The unique key
    (amazon_order_id, order_item_id) skips existing rows, including duplicates within the report.
    Returns the number of rows inserted.
    """
    fixed = {"region": region, "marketplace_id": marketplace_id, "amazon_report_id": amazon_report_id}
    for start in range(0, len(rows), CHUNK_SIZE):
        chunk = [{**fields, **fixed} for fields in rows[start : start + CHUNK_SIZE]]
        stmt = insert(OrderReportItem).values(chunk)
        # No-op on a duplicate key: keeps the stored row, without INSERT IGNORE hiding other errors.
        db.execute(stmt.on_duplicate_key_update(id=OrderReportItem.id))
    db.commit()
    # The driver reports duplicates as affected rows (FOUND_ROWS), so count what this report added.
    return db.scalar(
        select(func.count()).select_from(OrderReportItem).where(OrderReportItem.amazon_report_id == amazon_report_id)
    ) or 0


def summary_by_marketplace(db: Session) -> list[dict]:
    """Row count, distinct orders and date span per (region, marketplace)."""
    stmt = (
        select(
            OrderReportItem.region,
            OrderReportItem.marketplace_id,
            func.count().label("row_count"),
            func.count(func.distinct(OrderReportItem.amazon_order_id)).label("order_count"),
            func.min(OrderReportItem.purchase_date).label("first_purchase_date"),
            func.max(OrderReportItem.purchase_date).label("last_purchase_date"),
            func.max(OrderReportItem.created_at).label("last_stored_at"),
        )
        .group_by(OrderReportItem.region, OrderReportItem.marketplace_id)
        .order_by(OrderReportItem.region, OrderReportItem.marketplace_id)
    )
    return [dict(row._mapping) for row in db.execute(stmt)]
