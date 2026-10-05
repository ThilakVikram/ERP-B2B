"""Data Kiosk queries we support in the economics dataset (analytics_economics_2024_03_15).
Add a type here only together with its query module."""

from enum import Enum


class EconomicsQueryType(str, Enum):
    # Stored in amazon_intg_reports.report_type, next to Reports API types, since both share one queue.
    SKU_ECONOMICS = "DATA_KIOSK_SKU_ECONOMICS"
