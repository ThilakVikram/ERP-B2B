"""Economics dataset (analytics_economics_2024_03_15). One module per supported query."""

from app.integration.amazon.data_kiosk.economics.query_types import EconomicsQueryType
from app.integration.amazon.data_kiosk.economics.sku_economics import (
    COST_TYPES,
    AdCharge,
    CostItem,
    FeeCharge,
    SkuEconomicsQuery,
    SkuEconomicsRow,
    build_query,
)

__all__ = [
    "COST_TYPES",
    "AdCharge",
    "CostItem",
    "EconomicsQueryType",
    "FeeCharge",
    "SkuEconomicsQuery",
    "SkuEconomicsRow",
    "build_query",
]
