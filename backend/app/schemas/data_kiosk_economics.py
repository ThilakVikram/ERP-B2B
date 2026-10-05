from datetime import date, datetime
from decimal import Decimal

from app.integration.amazon.marketplaces import Region
from app.schemas.base import CamelModel


class SkuEconomicsSummaryOut(CamelModel):
    """Stored SKU economics for one marketplace."""

    region: Region
    marketplace_id: str
    row_count: int
    sku_count: int
    first_date: date | None
    last_date: date | None
    currency_code: str | None
    net_units_sold: int
    net_product_sales: Decimal
    net_proceeds_total: Decimal
    last_updated_at: datetime | None


class SkuEconomicsFeeOut(CamelModel):
    fee_type_name: str | None
    charge_identifier: str | None
    quantity: int | None
    amount: Decimal | None
    currency_code: str | None


class SkuEconomicsAdOut(CamelModel):
    ad_type_name: str | None
    quantity: int | None
    amount: Decimal | None
    currency_code: str | None


class SkuEconomicsCostOut(CamelModel):
    cost_type: str
    amount: Decimal | None
    currency_code: str | None


class SkuEconomicsOut(CamelModel):
    id: int
    data_kiosk_query_id: int  # the Data Kiosk query that last wrote the row
    region: Region
    marketplace_id: str
    start_date: date
    end_date: date
    msku: str
    fnsku: str
    parent_asin: str | None
    child_asin: str | None
    currency_code: str | None
    units_ordered: int | None
    units_refunded: int | None
    net_units_sold: int | None
    ordered_product_sales: Decimal | None
    refunded_product_sales: Decimal | None
    net_product_sales: Decimal | None
    total_fees: Decimal | None
    total_ad_spend: Decimal | None
    total_cost: Decimal | None
    net_proceeds_total: Decimal | None
    net_proceeds_per_unit: Decimal | None
    fees: list[SkuEconomicsFeeOut]  # from amazon_intg_sku_economics_fees
    ads: list[SkuEconomicsAdOut]  # from amazon_intg_sku_economics_ads
    costs: list[SkuEconomicsCostOut]  # from amazon_intg_sku_economics_costs
    created_at: datetime
    updated_at: datetime
