"""Amazon Selling Partner API integration (built on the amzn-sp-api SDK).

Layout:
    config.py        AmazonCredentials (env defaults or per-seller)
    client.py        SDK client factory + retry on throttling
    marketplaces.py  Marketplace IDs / regions
    exceptions.py    Integration errors
    reports/         Reports API: report types, ReportsService, document parsing
    data_kiosk/      Data Kiosk API (GraphQL queries): KioskService, one folder per dataset
    sellers/         Sellers API v1: SellersService (marketplace participations)
    inventory/       FBA Inventory API v1: FbaInventoryService (inventory summaries)
Add further SP-API sections (orders/, catalog/, finances/, ...) as sibling packages.
"""

from app.integration.amazon.config import AmazonCredentials, configured_regions
from app.integration.amazon.exceptions import (
    AmazonApiError,
    AmazonConfigError,
    AmazonIntegrationError,
    QueryProcessingError,
    ReportProcessingError,
    ReportTimeoutError,
)
from app.integration.amazon.marketplaces import Marketplace, Region

__all__ = [
    "AmazonApiError",
    "AmazonConfigError",
    "AmazonCredentials",
    "AmazonIntegrationError",
    "Marketplace",
    "QueryProcessingError",
    "Region",
    "ReportProcessingError",
    "ReportTimeoutError",
    "configured_regions",
]
