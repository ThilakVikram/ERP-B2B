"""Syncs FBA Inventory API v1 getInventorySummaries into the database, per marketplace."""

import logging
from datetime import datetime, timezone

from fastapi import HTTPException, status
from spapi.models.fba_inventory_v1 import InventorySummary
from sqlalchemy.orm import Session

from app.integration.amazon import AmazonApiError, AmazonConfigError, AmazonCredentials, Marketplace, Region
from app.integration.amazon.inventory import FbaInventoryService
from app.repositories import fba_inventory_summary_repository
from app.schemas.inventory import FbaInventorySummaryOut, FbaInventorySyncOut

logger = logging.getLogger(__name__)


def _marketplace(marketplace_id: str) -> Marketplace:
    for marketplace in Marketplace:
        if marketplace.marketplace_id == marketplace_id:
            return marketplace
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unknown marketplace ID {marketplace_id!r}",
    )


def _naive_utc(dt: datetime | str | None) -> datetime | None:
    # The SDK can hand back lastUpdatedTime as an ISO 8601 string (or "").
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00")) if dt else None
        except ValueError:
            return None
    if dt is None or dt.tzinfo is None:
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def _to_row(s: InventorySummary, synced_at: datetime) -> dict:
    details = s.inventory_details
    reserved = details and details.reserved_quantity
    researching = details and details.researching_quantity
    unfulfillable = details and details.unfulfillable_quantity

    def qty(obj, attr: str) -> int:
        return (getattr(obj, attr, None) or 0) if obj else 0

    return {
        "seller_sku": s.seller_sku,
        "asin": s.asin,
        "fn_sku": s.fn_sku,
        "condition": s.condition,
        "product_name": s.product_name,
        "total_quantity": s.total_quantity or 0,
        "stores": s.stores,
        "last_updated_time": _naive_utc(s.last_updated_time),
        "fulfillable_quantity": qty(details, "fulfillable_quantity"),
        "inbound_working_quantity": qty(details, "inbound_working_quantity"),
        "inbound_shipped_quantity": qty(details, "inbound_shipped_quantity"),
        "inbound_receiving_quantity": qty(details, "inbound_receiving_quantity"),
        "total_reserved_quantity": qty(reserved, "total_reserved_quantity"),
        "pending_customer_order_quantity": qty(reserved, "pending_customer_order_quantity"),
        "pending_transshipment_quantity": qty(reserved, "pending_transshipment_quantity"),
        "fc_processing_quantity": qty(reserved, "fc_processing_quantity"),
        "total_researching_quantity": qty(researching, "total_researching_quantity"),
        "researching_quantity_breakdown": (
            [{"name": e.name, "quantity": e.quantity} for e in researching.researching_quantity_breakdown]
            if researching and researching.researching_quantity_breakdown
            else None
        ),
        "total_unfulfillable_quantity": qty(unfulfillable, "total_unfulfillable_quantity"),
        "customer_damaged_quantity": qty(unfulfillable, "customer_damaged_quantity"),
        "warehouse_damaged_quantity": qty(unfulfillable, "warehouse_damaged_quantity"),
        "distributor_damaged_quantity": qty(unfulfillable, "distributor_damaged_quantity"),
        "carrier_damaged_quantity": qty(unfulfillable, "carrier_damaged_quantity"),
        "defective_quantity": qty(unfulfillable, "defective_quantity"),
        "expired_quantity": qty(unfulfillable, "expired_quantity"),
        "last_synced_at": synced_at,
    }


def sync_marketplace(db: Session, marketplace_id: str) -> FbaInventorySyncOut:
    """Fetch every inventory summary for the marketplace and replace that marketplace's rows."""
    marketplace = _marketplace(marketplace_id)
    region = marketplace.region
    try:
        service = FbaInventoryService(AmazonCredentials.for_marketplace(marketplace))
        summaries = service.get_inventory_summaries(marketplace_id)
    except AmazonConfigError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except AmazonApiError as exc:
        logger.error("getInventorySummaries sync for %s (%s) failed: %s", marketplace_id, region.value, exc)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    synced_at = datetime.now(timezone.utc).replace(tzinfo=None)
    rows = [_to_row(s, synced_at) for s in summaries if s.seller_sku]
    count = fba_inventory_summary_repository.replace_marketplace(db, region.value, marketplace_id, rows)
    logger.info("Synced %d FBA inventory summaries for %s (%s)", count, marketplace_id, region.value)
    return FbaInventorySyncOut(region=region, marketplace_id=marketplace_id, count=count, synced_at=synced_at)


def list_summaries(
    db: Session, region: Region | None = None, marketplace_id: str | None = None
) -> list[FbaInventorySummaryOut]:
    rows = fba_inventory_summary_repository.list_all(db, region.value if region else None, marketplace_id)
    return [FbaInventorySummaryOut.model_validate(s) for s in rows]
