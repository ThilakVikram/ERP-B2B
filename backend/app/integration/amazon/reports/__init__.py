"""SP-API Reports API (2021-06-30).

Layout:
    service.py   ReportsService: create / poll / download any report (generic)
    document.py  Document download, decompression and TSV/CSV/JSON parsing
    fields.py    Flat-file cell parsers shared by the report packages
    order/       Order reports (one module per supported report type)
    listing/     Listing (inventory) reports
Add further categories (fba/, inventory/, returns/, ...) as sibling packages, with only the
report types we actually use.
"""

from app.integration.amazon.reports.document import ReportFormat, ReportResult
from app.integration.amazon.reports.service import ProcessingStatus, ReportsService

__all__ = [
    "ProcessingStatus",
    "ReportFormat",
    "ReportResult",
    "ReportsService",
]
