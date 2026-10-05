from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class OrderReportItem(Base):
    """One order line from GET_FLAT_FILE_ALL_ORDERS_DATA_BY_ORDER_DATE_GENERAL (older rows came from BY_LAST_UPDATE).

    An order item (amazon_order_id + order_item_id) is stored once; rows already stored are skipped, not updated.
    `raw` keeps the full report row, since columns vary by marketplace.
    """

    __tablename__ = "amazon_intg_order_report_items"
    __table_args__ = (
        UniqueConstraint("amazon_order_id", "order_item_id", name="uq_amazon_intg_order_report_items_order_item"),
        # Covers the per-marketplace summary (rows, distinct orders, purchase date span, last stored),
        # so it is read from this index instead of scanning the large rows (raw JSON).
        Index(
            "ix_amazon_intg_order_report_items_summary",
            "region",
            "marketplace_id",
            "amazon_order_id",
            "purchase_date",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    amazon_report_id: Mapped[int] = mapped_column(ForeignKey("amazon_intg_reports.id"), index=True)
    region: Mapped[str] = mapped_column(String(2), index=True)  # NA | EU | FE
    marketplace_id: Mapped[str] = mapped_column(String(20), index=True)

    amazon_order_id: Mapped[str] = mapped_column(String(50), index=True)
    order_item_id: Mapped[str] = mapped_column(String(50))
    merchant_order_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    purchase_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_updated_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    order_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fulfillment_channel: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sales_channel: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ship_service_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    product_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Amazon SKUs are case-sensitive; MySQL's default collation is not.
    sku: Mapped[str] = mapped_column(String(255, collation="utf8mb4_bin"))
    asin: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    item_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    item_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    item_tax: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    shipping_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    shipping_tax: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    gift_wrap_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    gift_wrap_tax: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    item_promotion_discount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    ship_promotion_discount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    ship_city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ship_state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ship_postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ship_country: Mapped[str | None] = mapped_column(String(2), nullable=True)
    promotion_ids: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_business_order: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    raw: Mapped[dict] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
