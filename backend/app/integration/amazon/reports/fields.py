"""Parsers for flat-file (TSV/CSV) report cells. Empty or malformed cells become None."""

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation


def normalize_row(row: dict) -> dict[str, str]:
    """Lowercase the headers and drop a leading byte-order mark; csv puts surplus cells under the key None."""
    return {(k or "_extra").strip("﻿ \t").lower(): v for k, v in row.items() if k is not None or v}


def to_str(value: str | None, max_len: int | None = None) -> str | None:
    value = (value or "").strip()
    if not value:
        return None
    return value[:max_len] if max_len else value


def to_int(value: str | None) -> int | None:
    try:
        return int(Decimal(value.strip())) if value and value.strip() else None
    except InvalidOperation:
        return None


def to_decimal(value: str | None) -> Decimal | None:
    try:
        return Decimal(value.strip().replace(",", "")) if value and value.strip() else None
    except InvalidOperation:
        return None


def to_datetime(value: str | None) -> datetime | None:
    """ISO 8601 with offset (e.g. 2026-09-20T10:15:30+00:00) -> naive UTC."""
    try:
        dt = datetime.fromisoformat(value.strip().replace("Z", "+00:00")) if value and value.strip() else None
    except ValueError:
        return None
    if dt is not None and dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def to_bool(value: str | None) -> bool | None:
    return {"true": True, "false": False}.get((value or "").strip().lower())
