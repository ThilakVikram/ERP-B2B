from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

Money = Numeric(16, 4)


class SkuEconomics(Base):
    """One SKU's economics for a period, from the Data Kiosk SKU Economics query
    (analytics_economics_2024_03_15). Amounts are in `currency_code`.

    Amazon can revise a period's fees and sales, so a later query for the same
    (marketplace, SKU, FNSKU, period) updates the stored row and replaces its breakdown rows;
    data_kiosk_query_id is the Data Kiosk query that last wrote it. The breakdowns live in their own
    tables (fees, ads, costs); total_fees / total_ad_spend / total_cost are their sums.
    """

    __tablename__ = "amazon_intg_sku_economics"
    __table_args__ = (
        UniqueConstraint(
            "marketplace_id", "msku", "fnsku", "start_date", "end_date", name="uq_amazon_intg_sku_economics_marketplace_sku_period"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    data_kiosk_query_id: Mapped[int] = mapped_column(ForeignKey("amazon_intg_data_kiosk_queries.id"), index=True)
    region: Mapped[str] = mapped_column(String(2), index=True)  # NA | EU | FE
    marketplace_id: Mapped[str] = mapped_column(String(20), index=True)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)

    # Amazon SKUs are case-sensitive; MySQL's default collation is not.
    msku: Mapped[str] = mapped_column(String(255, collation="utf8mb4_bin"))
    fnsku: Mapped[str] = mapped_column(String(20), default="")
    parent_asin: Mapped[str | None] = mapped_column(String(20), nullable=True)
    child_asin: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    currency_code: Mapped[str | None] = mapped_column(String(3), nullable=True)

    units_ordered: Mapped[int | None] = mapped_column(Integer, nullable=True)
    units_refunded: Mapped[int | None] = mapped_column(Integer, nullable=True)
    net_units_sold: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ordered_product_sales: Mapped[Decimal | None] = mapped_column(Money, nullable=True)
    refunded_product_sales: Mapped[Decimal | None] = mapped_column(Money, nullable=True)
    net_product_sales: Mapped[Decimal | None] = mapped_column(Money, nullable=True)
    total_fees: Mapped[Decimal | None] = mapped_column(Money, nullable=True)
    total_ad_spend: Mapped[Decimal | None] = mapped_column(Money, nullable=True)
    total_cost: Mapped[Decimal | None] = mapped_column(Money, nullable=True)
    net_proceeds_total: Mapped[Decimal | None] = mapped_column(Money, nullable=True)
    net_proceeds_per_unit: Mapped[Decimal | None] = mapped_column(Money, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    fees: Mapped[list["SkuEconomicsFee"]] = relationship(
        back_populates="sku_economics", cascade="all, delete-orphan", passive_deletes=True, lazy="selectin"
    )
    ads: Mapped[list["SkuEconomicsAd"]] = relationship(
        back_populates="sku_economics", cascade="all, delete-orphan", passive_deletes=True, lazy="selectin"
    )
    costs: Mapped[list["SkuEconomicsCost"]] = relationship(
        back_populates="sku_economics", cascade="all, delete-orphan", passive_deletes=True, lazy="selectin"
    )


class SkuEconomicsFee(Base):
    """One charge of a fee type for a SKU period (a fee type can have several charges)."""

    __tablename__ = "amazon_intg_sku_economics_fees"

    id: Mapped[int] = mapped_column(primary_key=True)
    sku_economics_id: Mapped[int] = mapped_column(ForeignKey("amazon_intg_sku_economics.id", ondelete="CASCADE"), index=True)
    fee_type_name: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    charge_identifier: Mapped[str | None] = mapped_column(String(100), nullable=True)
    quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    amount: Mapped[Decimal | None] = mapped_column(Money, nullable=True)
    currency_code: Mapped[str | None] = mapped_column(String(3), nullable=True)

    sku_economics: Mapped[SkuEconomics] = relationship(back_populates="fees")


class SkuEconomicsAd(Base):
    """One ad charge (by ad type) for a SKU period."""

    __tablename__ = "amazon_intg_sku_economics_ads"

    id: Mapped[int] = mapped_column(primary_key=True)
    sku_economics_id: Mapped[int] = mapped_column(ForeignKey("amazon_intg_sku_economics.id", ondelete="CASCADE"), index=True)
    ad_type_name: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    amount: Mapped[Decimal | None] = mapped_column(Money, nullable=True)
    currency_code: Mapped[str | None] = mapped_column(String(3), nullable=True)

    sku_economics: Mapped[SkuEconomics] = relationship(back_populates="ads")


class SkuEconomicsCost(Base):
    """One cost item for a SKU period. cost_type: COST_OF_GOODS_SOLD | FBA_SHIPPING_TO_AMAZON |
    MFN_FULFILLMENT | MFN_STORAGE | MISCELLANEOUS."""

    __tablename__ = "amazon_intg_sku_economics_costs"

    id: Mapped[int] = mapped_column(primary_key=True)
    sku_economics_id: Mapped[int] = mapped_column(ForeignKey("amazon_intg_sku_economics.id", ondelete="CASCADE"), index=True)
    cost_type: Mapped[str] = mapped_column(String(30), index=True)
    amount: Mapped[Decimal | None] = mapped_column(Money, nullable=True)
    currency_code: Mapped[str | None] = mapped_column(String(3), nullable=True)

    sku_economics: Mapped[SkuEconomics] = relationship(back_populates="costs")
