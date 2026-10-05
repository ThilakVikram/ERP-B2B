"""SP-API Data Kiosk API (2023-11-15): GraphQL queries over Amazon datasets.

Layout:
    service.py   KioskService: create / poll / cancel queries, download JSONL documents, pagination
    document.py  Document download and JSONL parsing
    economics/   analytics_economics_2024_03_15 dataset (one module per query we use)
Add further datasets (sales_and_traffic/, vendor/, ...) as sibling packages.
"""

from app.integration.amazon.data_kiosk.service import KioskService, QueryStatus, compact

__all__ = ["KioskService", "QueryStatus", "compact"]
