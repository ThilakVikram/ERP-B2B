from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.amazon.marketplace import AmazonMarketplace


class AmazonItem(Base):
    """One item (SKU) the seller sells in a marketplace. The app's own record, kept apart from the raw
    integration tables (amazon_intg_*); order items reference it by id."""

    __tablename__ = "amazon_items"
    __table_args__ = (
        UniqueConstraint("amazon_marketplace_id", "seller_sku", name="uq_amazon_items_marketplace_sku"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    amazon_marketplace_id: Mapped[int] = mapped_column(ForeignKey("amazon_marketplaces.id"), index=True)
    # The integration listing this item came from; None when it is not (or no longer) in the integration data.
    integration_id: Mapped[int | None] = mapped_column(
        ForeignKey("amazon_intg_merchant_listings.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Amazon SKUs are case-sensitive; MySQL's default collation is not.
    seller_sku: Mapped[str] = mapped_column(String(255, collation="utf8mb4_bin"))
    asin: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    fn_sku: Mapped[str | None] = mapped_column(String(50), nullable=True)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    item_condition: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fulfillment_channel: Mapped[str | None] = mapped_column(String(50), nullable=True)
    price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    currency_code: Mapped[str | None] = mapped_column(String(3), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    status: Mapped[str | None] = mapped_column(String(20), nullable=True)  # e.g. Active | Inactive
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    marketplace: Mapped[AmazonMarketplace] = relationship(back_populates="items")
