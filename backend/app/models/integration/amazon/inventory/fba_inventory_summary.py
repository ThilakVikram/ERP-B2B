from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FbaInventorySummary(Base):
    """One SKU's FBA inventory in one marketplace, from FBA Inventory API v1 getInventorySummaries.

    inventoryDetails (reserved / researching / unfulfillable quantities) is flattened into columns.
    """

    __tablename__ = "amazon_intg_fba_inventory_summaries"
    __table_args__ = (
        UniqueConstraint("region", "marketplace_id", "seller_sku", name="uq_amazon_intg_fba_inventory_summaries_region_marketplace_sku"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    region: Mapped[str] = mapped_column(String(2), index=True)  # NA | EU | FE
    marketplace_id: Mapped[str] = mapped_column(String(20), index=True)

    # Amazon SKUs are case-sensitive (ABC and Abc are different SKUs); MySQL's default collation is not.
    seller_sku: Mapped[str] = mapped_column(String(255, collation="utf8mb4_bin"))
    asin: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    fn_sku: Mapped[str | None] = mapped_column(String(50), nullable=True)
    condition: Mapped[str | None] = mapped_column(String(50), nullable=True)
    product_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    total_quantity: Mapped[int] = mapped_column(Integer, default=0)
    stores: Mapped[list[str] | None] = mapped_column(JSON(none_as_null=True), nullable=True)
    last_updated_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # inventoryDetails
    fulfillable_quantity: Mapped[int] = mapped_column(Integer, default=0)
    inbound_working_quantity: Mapped[int] = mapped_column(Integer, default=0)
    inbound_shipped_quantity: Mapped[int] = mapped_column(Integer, default=0)
    inbound_receiving_quantity: Mapped[int] = mapped_column(Integer, default=0)
    # inventoryDetails.reservedQuantity
    total_reserved_quantity: Mapped[int] = mapped_column(Integer, default=0)
    pending_customer_order_quantity: Mapped[int] = mapped_column(Integer, default=0)
    pending_transshipment_quantity: Mapped[int] = mapped_column(Integer, default=0)
    fc_processing_quantity: Mapped[int] = mapped_column(Integer, default=0)
    # inventoryDetails.researchingQuantity
    total_researching_quantity: Mapped[int] = mapped_column(Integer, default=0)
    researching_quantity_breakdown: Mapped[list[dict] | None] = mapped_column(JSON(none_as_null=True), nullable=True)
    # inventoryDetails.unfulfillableQuantity
    total_unfulfillable_quantity: Mapped[int] = mapped_column(Integer, default=0)
    customer_damaged_quantity: Mapped[int] = mapped_column(Integer, default=0)
    warehouse_damaged_quantity: Mapped[int] = mapped_column(Integer, default=0)
    distributor_damaged_quantity: Mapped[int] = mapped_column(Integer, default=0)
    carrier_damaged_quantity: Mapped[int] = mapped_column(Integer, default=0)
    defective_quantity: Mapped[int] = mapped_column(Integer, default=0)
    expired_quantity: Mapped[int] = mapped_column(Integer, default=0)

    last_synced_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
