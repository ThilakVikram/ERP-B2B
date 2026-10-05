"""SKU Economics: sales, fees, ad spend, costs and net proceeds per SKU for a period.

Schema: analytics_economics_2024_03_15, query `economics(startDate, endDate, marketplaceIds)`.
Without aggregateBy, Amazon returns one record per SKU for the whole requested period.
Docs: https://developer-docs.amazon.com/sp-api/docs/data-kiosk-api

    economics = SkuEconomicsQuery(AmazonCredentials.for_marketplace(Marketplace.US))
    query_id = economics.request(date(2026, 1, 1), date(2026, 1, 10), [Marketplace.US.marketplace_id])
    rows = economics.download_rows(economics.wait(query_id))   # blocking: run in a background task
"""

import json
import logging
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from spapi.models.datakiosk_v2023_11_15 import Query

from app.integration.amazon.config import AmazonCredentials
from app.integration.amazon.data_kiosk.economics.query_types import EconomicsQueryType
from app.integration.amazon.data_kiosk.service import KioskService

logger = logging.getLogger(__name__)

SCHEMA = "analytics_economics_2024_03_15"

# The SKU Economics query, verbatim; build_query() fills the three empty arguments.
QUERY_TEMPLATE = (
    'query skuEconomics{analytics_economics_2024_03_15{economics(endDate:"",marketplaceIds:"",startDate:"")'
    "{ads{adTypeName charge{quantity totalAmount{amount currencyCode}}}childAsin endDate "
    "cost{costOfGoodsSold{amount currencyCode}fbaCost{shippingToAmazonCost{amount currencyCode}}"
    "mfnCost{fulfillmentCost{amount currencyCode}storageCost{amount currencyCode}}miscellaneousCost{amount currencyCode}}"
    "fees{feeTypeName charges{identifier aggregatedDetail{quantity totalAmount{amount currencyCode}}}}"
    "fnsku marketplaceId msku netProceeds{total{amount currencyCode}perUnit{amount currencyCode}}"
    "parentAsin sales{netUnitsSold unitsOrdered unitsRefunded netProductSales{amount currencyCode}"
    "orderedProductSales{amount currencyCode}refundedProductSales{amount currencyCode}}startDate}}}"
)
_ARGUMENTS = 'endDate:"",marketplaceIds:"",startDate:""'


def build_query(start: date, end: date, marketplace_ids: Sequence[str]) -> str:
    """QUERY_TEMPLATE with the period and marketplaces filled in. json.dumps gives valid GraphQL
    literals; marketplaceIds is a list ([String!]!), e.g. ["ATVPDKIKX0DER"]."""
    arguments = (
        f"endDate:{json.dumps(end.isoformat())},"
        f"marketplaceIds:{json.dumps(list(marketplace_ids))},"
        f"startDate:{json.dumps(start.isoformat())}"
    )
    return QUERY_TEMPLATE.replace(_ARGUMENTS, arguments, 1)


def _get(obj: Any, *path: str) -> Any:
    for key in path:
        if not isinstance(obj, dict):
            return None
        obj = obj.get(key)
    return obj


def _amount(money: Any) -> Decimal | None:
    value = _get(money, "amount")
    try:
        return Decimal(str(value)) if value is not None else None
    except InvalidOperation:
        return None


def _sum(amounts: Iterable[Decimal | None]) -> Decimal | None:
    values = [a for a in amounts if a is not None]
    return sum(values, Decimal(0)) if values else None


def _date(value: Any) -> date | None:
    try:
        return date.fromisoformat(str(value)[:10]) if value else None
    except ValueError:
        return None


def _int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


@dataclass
class FeeCharge:
    """One charge of a fee type (a fee can have several charges)."""

    fee_type_name: str | None
    charge_identifier: str | None
    quantity: int | None
    amount: Decimal | None
    currency_code: str | None


@dataclass
class AdCharge:
    ad_type_name: str | None
    quantity: int | None
    amount: Decimal | None
    currency_code: str | None


@dataclass
class CostItem:
    cost_type: str  # one of COST_TYPES
    amount: Decimal | None
    currency_code: str | None


# cost_type -> path of the money object inside the record's `cost`.
COST_TYPES: dict[str, tuple[str, ...]] = {
    "COST_OF_GOODS_SOLD": ("costOfGoodsSold",),
    "FBA_SHIPPING_TO_AMAZON": ("fbaCost", "shippingToAmazonCost"),
    "MFN_FULFILLMENT": ("mfnCost", "fulfillmentCost"),
    "MFN_STORAGE": ("mfnCost", "storageCost"),
    "MISCELLANEOUS": ("miscellaneousCost",),
}


def _fee_charges(fees: list) -> list[FeeCharge]:
    return [
        FeeCharge(
            fee_type_name=fee.get("feeTypeName"),
            charge_identifier=charge.get("identifier"),
            quantity=_int(_get(charge, "aggregatedDetail", "quantity")),
            amount=_amount(_get(charge, "aggregatedDetail", "totalAmount")),
            currency_code=_get(charge, "aggregatedDetail", "totalAmount", "currencyCode"),
        )
        for fee in fees
        for charge in (fee.get("charges") or [])
    ]


def _ad_charges(ads: list) -> list[AdCharge]:
    return [
        AdCharge(
            ad_type_name=ad.get("adTypeName"),
            quantity=_int(_get(ad, "charge", "quantity")),
            amount=_amount(_get(ad, "charge", "totalAmount")),
            currency_code=_get(ad, "charge", "totalAmount", "currencyCode"),
        )
        for ad in ads
    ]


def _cost_items(cost: dict) -> list[CostItem]:
    items = []
    for cost_type, path in COST_TYPES.items():
        money = _get(cost, *path)
        if _amount(money) is not None:
            items.append(CostItem(cost_type=cost_type, amount=_amount(money), currency_code=_get(money, "currencyCode")))
    return items


@dataclass
class SkuEconomicsRow:
    """One SKU's economics for a period. Money is in `currency_code`. Fee charges, ad charges and
    cost items are separate lists (stored in their own tables); the totals are their sums."""

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
    total_fees: Decimal | None  # sum of fee charges
    total_ad_spend: Decimal | None  # sum of ad charges
    total_cost: Decimal | None  # sum of cost items
    net_proceeds_total: Decimal | None
    net_proceeds_per_unit: Decimal | None
    fees: list[FeeCharge]
    ads: list[AdCharge]
    costs: list[CostItem]

    @classmethod
    def from_record(cls, r: dict) -> "SkuEconomicsRow | None":
        """Parse one record. None for records without a marketplace or period."""
        marketplace_id, start, end = r.get("marketplaceId"), _date(r.get("startDate")), _date(r.get("endDate"))
        if not marketplace_id or not start or not end:
            return None
        sales = r.get("sales") or {}
        fees = _fee_charges(r.get("fees") or [])
        ads = _ad_charges(r.get("ads") or [])
        costs = _cost_items(r.get("cost") or {})
        currency = (
            _get(sales, "netProductSales", "currencyCode")
            or _get(r, "netProceeds", "total", "currencyCode")
            or _get(sales, "orderedProductSales", "currencyCode")
        )
        return cls(
            marketplace_id=marketplace_id,
            start_date=start,
            end_date=end,
            msku=(r.get("msku") or "")[:255],
            fnsku=(r.get("fnsku") or "")[:20],
            parent_asin=r.get("parentAsin"),
            child_asin=r.get("childAsin"),
            currency_code=currency,
            units_ordered=_int(sales.get("unitsOrdered")),
            units_refunded=_int(sales.get("unitsRefunded")),
            net_units_sold=_int(sales.get("netUnitsSold")),
            ordered_product_sales=_amount(sales.get("orderedProductSales")),
            refunded_product_sales=_amount(sales.get("refundedProductSales")),
            net_product_sales=_amount(sales.get("netProductSales")),
            total_fees=_sum(f.amount for f in fees),
            total_ad_spend=_sum(a.amount for a in ads),
            total_cost=_sum(c.amount for c in costs),
            net_proceeds_total=_amount(_get(r, "netProceeds", "total")),
            net_proceeds_per_unit=_amount(_get(r, "netProceeds", "perUnit")),
            fees=fees,
            ads=ads,
            costs=costs,
        )


def _economics_records(record: dict) -> list[dict]:
    """A JSONL line is one economics record; unwrap it if Amazon nests it under the schema."""
    economics = _get(record, SCHEMA, "economics")
    if economics is None:
        return [record]
    return economics if isinstance(economics, list) else [economics]


class SkuEconomicsQuery:
    """Requests, waits for and parses the SKU Economics query (all result pages)."""

    QUERY_TYPE = EconomicsQueryType.SKU_ECONOMICS

    def __init__(self, credentials: AmazonCredentials | None = None, service: KioskService | None = None):
        self.service = service or KioskService(credentials)

    def request(self, start: date, end: date, marketplace_ids: Sequence[str]) -> str:
        """Submit the query for [start, end] (whole days). Returns the queryId."""
        if end < start:
            raise ValueError("end must be on or after start")
        return self.service.create_query(build_query(start, end, marketplace_ids))

    def wait(
        self,
        query_id: str,
        poll_interval: float = 30.0,
        timeout: float = 60 * 60,
        on_status: Callable[[str], None] | None = None,
    ) -> Query:
        return self.service.wait_for_query(query_id, poll_interval=poll_interval, timeout=timeout, on_status=on_status)

    def download_rows(self, done: Query) -> list[SkuEconomicsRow]:
        """Rows of a DONE query, following every further result page."""
        records = [e for r in self.service.all_records(done) for e in _economics_records(r)]
        rows = [row for row in map(SkuEconomicsRow.from_record, records) if row]
        logger.info("Parsed %d SKU economics rows from Data Kiosk query %s", len(rows), done.query_id)
        return rows
