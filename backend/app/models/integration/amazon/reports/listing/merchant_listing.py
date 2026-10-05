from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MerchantListing(Base):
    """One listing (SKU) of a marketplace from GET_MERCHANT_LISTINGS_ALL_DATA.

    The report is a snapshot, so each new report updates the stored row for (region, marketplace, SKU);
    amazon_report_id is the report that last wrote it. `raw` keeps the full report row, since
    columns vary by marketplace.
    """

    __tablename__ = "amazon_intg_merchant_listings"
    __table_args__ = (
        UniqueConstraint("region", "marketplace_id", "seller_sku", name="uq_amazon_intg_merchant_listings_region_marketplace_sku"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    amazon_report_id: Mapped[int] = mapped_column(ForeignKey("amazon_intg_reports.id"), index=True)
    # The app item created from this row (the other side of amazon_items.integration_id);
    # None until items are synced. use_alter: the two tables reference each other.
    amazon_item_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "amazon_items.id",
            ondelete="SET NULL",
            use_alter=True,
            name="fk_amazon_intg_merchant_listings_amazon_item_id",
        ),
        nullable=True,
        index=True,
    )
    region: Mapped[str] = mapped_column(String(2), index=True)  # NA | EU | FE
    marketplace_id: Mapped[str] = mapped_column(String(20), index=True)

    # Amazon SKUs are case-sensitive; MySQL's default collation is not.
    seller_sku: Mapped[str] = mapped_column(String(255, collation="utf8mb4_bin"))
    listing_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    item_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    item_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    asin: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)  # asin1
    product_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    product_id_type: Mapped[str | None] = mapped_column(String(10), nullable=True)
    price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pending_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    open_date: Mapped[str | None] = mapped_column(String(50), nullable=True)  # e.g. "2024-01-15 10:22:33 PST"
    image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    item_condition: Mapped[str | None] = mapped_column(String(10), nullable=True)
    item_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    fulfillment_channel: Mapped[str | None] = mapped_column(String(50), nullable=True)
    merchant_shipping_group: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    raw: Mapped[dict] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
