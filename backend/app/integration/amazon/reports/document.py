"""Download, decompress, decode and parse SP-API report documents."""

import csv
import gzip
import io
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any

import requests
from spapi.models.reports_v2021_06_30 import Report, ReportDocument

from app.integration.amazon.exceptions import AmazonApiError

DOWNLOAD_TIMEOUT_SECONDS = 300


class ReportFormat(str, Enum):
    TSV = "tsv"  # most GET_FLAT_FILE_* / GET_MERCHANT_* / FBA reports
    CSV = "csv"
    JSON = "json"  # analytics (Brand Analytics, Sales & Traffic, Vendor)
    XML = "xml"
    BINARY = "binary"  # PDFs / zips (e.g. Easy Ship documents)


@dataclass
class ReportResult:
    """A downloaded report. `content` is the raw, already-decompressed document."""

    report: Report | None
    document: ReportDocument
    content: bytes
    encoding: str | None = None

    @property
    def report_type(self) -> str | None:
        return self.report.report_type if self.report else None

    @property
    def text(self) -> str:
        return decode_content(self.content, self.encoding)

    @property
    def format(self) -> ReportFormat:
        return detect_format(self.content, self.report_type)

    def rows(self) -> list[dict[str, str]]:
        """Parse a TSV/CSV report into one dict per row (keyed by header)."""
        fmt = self.format
        if fmt not in (ReportFormat.TSV, ReportFormat.CSV):
            raise ValueError(f"rows() needs a TSV/CSV report, this one is {fmt.value}")
        delimiter = "," if fmt is ReportFormat.CSV else "\t"
        return list(csv.DictReader(io.StringIO(self.text), delimiter=delimiter))

    def json(self) -> Any:
        return json.loads(self.text)

    def parse(self) -> Any:
        """rows() for flat files, json() for JSON, text for XML, raw bytes for binary."""
        fmt = self.format
        if fmt in (ReportFormat.TSV, ReportFormat.CSV):
            return self.rows()
        if fmt is ReportFormat.JSON:
            return self.json()
        if fmt is ReportFormat.XML:
            return self.text
        return self.content


def download_document(document: ReportDocument) -> tuple[bytes, str | None]:
    """Fetch the pre-signed document URL. Returns (decompressed bytes, charset from Content-Type)."""
    try:
        resp = requests.get(document.url, timeout=DOWNLOAD_TIMEOUT_SECONDS)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise AmazonApiError(
            f"Failed to download report document {document.report_document_id}: {exc}",
            status=getattr(exc.response, "status_code", None),
        ) from exc

    content = resp.content
    if document.compression_algorithm == "GZIP":
        content = gzip.decompress(content)
    # Only trust an explicit charset; requests otherwise guesses ISO-8859-1 for text/*.
    charset = None
    if "charset=" in resp.headers.get("Content-Type", "").lower():
        charset = resp.encoding
    return content, charset


def decode_content(content: bytes, encoding: str | None = None) -> str:
    # Flat files come in UTF-8, Cp1252 or Shift_JIS depending on the marketplace.
    for enc in filter(None, (encoding, "utf-8-sig", "cp1252")):
        try:
            return content.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return content.decode("utf-8", errors="replace")


def detect_format(content: bytes, report_type: str | None = None) -> ReportFormat:
    head = content[:512].lstrip(b"\xef\xbb\xbf \t\r\n")
    if head.startswith((b"%PDF", b"PK\x03\x04")):
        return ReportFormat.BINARY
    if head[:1] in (b"{", b"["):
        return ReportFormat.JSON
    if head[:1] == b"<":
        return ReportFormat.XML
    if report_type and "_CSV_" in report_type:
        return ReportFormat.CSV
    return ReportFormat.TSV
