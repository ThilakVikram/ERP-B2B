"""Download and parse Data Kiosk documents (JSON Lines: one JSON object per line)."""

import gzip
import json
from typing import Any

import requests

from app.integration.amazon.exceptions import AmazonApiError

DOWNLOAD_TIMEOUT_SECONDS = 300


def download_text(document_id: str, url: str) -> str:
    """Fetch a document's pre-signed URL (valid for 5 minutes) and return its text."""
    try:
        resp = requests.get(url, timeout=DOWNLOAD_TIMEOUT_SECONDS)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise AmazonApiError(
            f"Failed to download Data Kiosk document {document_id}: {exc}",
            status=getattr(exc.response, "status_code", None),
        ) from exc
    content = resp.content
    if content[:2] == b"\x1f\x8b":  # gzip, in case Amazon compresses it
        content = gzip.decompress(content)
    return content.decode("utf-8-sig")


def parse_jsonl(text: str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in text.splitlines() if line.strip()]
