"""Data Kiosk API (2023-11-15) wrapper built on amzn-sp-api.

Data Kiosk runs GraphQL queries over Amazon's datasets (schemas). Like the Reports API it is
asynchronous: createQuery -> poll getQuery until DONE -> getDocument (JSONL). A result can span
several pages; each further page is a new createQuery with the same query and the previous
page's pagination.nextToken.

Generic plumbing only: each dataset lives in its own folder (e.g. data_kiosk/economics/) and uses
this service. wait_for_query() blocks (minutes); run it in a background worker.

Rate limits: createQuery and getDocument 0.0167/s (1 per minute, burst 15), getQuery 2/s.
"""

import logging
import re
import time
from collections.abc import Callable, Iterator, Sequence
from datetime import datetime, timezone
from typing import Any

from spapi import ApiClient
from spapi.api.datakiosk_v2023_11_15.queries_api import QueriesApi
from spapi.models.datakiosk_v2023_11_15 import CreateQuerySpecification, GetDocumentResponse, Query

from app.integration.amazon.client import build_api_client, call_with_retry
from app.integration.amazon.config import AmazonCredentials
from app.integration.amazon.exceptions import QueryProcessingError, ReportTimeoutError
from app.integration.amazon.data_kiosk.document import download_text, parse_jsonl

logger = logging.getLogger(__name__)

MAX_QUERY_LENGTH = 8000  # characters, after unnecessary whitespace is removed


class QueryStatus:
    CANCELLED = "CANCELLED"
    DONE = "DONE"
    FATAL = "FATAL"
    IN_PROGRESS = "IN_PROGRESS"
    IN_QUEUE = "IN_QUEUE"

    TERMINAL = frozenset({CANCELLED, DONE, FATAL})


def compact(query: str) -> str:
    """Collapse whitespace so the 8000-character limit is measured like Amazon does."""
    return re.sub(r"\s+", " ", query).strip()


def _utc(dt: datetime | None) -> datetime | None:
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class KioskService:
    """One instance per seller account (credentials). Safe to reuse across calls."""

    def __init__(self, credentials: AmazonCredentials | None = None, api_client: ApiClient | None = None):
        self.credentials = credentials or AmazonCredentials.from_env()
        self._api_client = api_client
        self._api: QueriesApi | None = None

    @property
    def api(self) -> QueriesApi:
        # Built lazily: creating the SDK client performs an LWA token request.
        if self._api is None:
            self._api = QueriesApi(self._api_client or build_api_client(self.credentials))
        return self._api

    # ---------- Queries ----------

    def create_query(self, query: str, pagination_token: str | None = None) -> str:
        """Submit a GraphQL query. Returns the queryId."""
        query = compact(query)
        if len(query) > MAX_QUERY_LENGTH:
            raise ValueError(f"Data Kiosk queries can be at most {MAX_QUERY_LENGTH} characters (got {len(query)})")
        body = CreateQuerySpecification(query=query, pagination_token=pagination_token)
        query_id = call_with_retry(self.api.create_query, body).query_id
        logger.info("Created Data Kiosk query %s%s", query_id, " (next page)" if pagination_token else "")
        return query_id

    def get_query(self, query_id: str) -> Query:
        return call_with_retry(self.api.get_query, query_id)

    def get_queries(
        self,
        processing_statuses: Sequence[str] | None = None,
        created_since: datetime | None = None,
        created_until: datetime | None = None,
        page_size: int = 100,
    ) -> Iterator[Query]:
        """Yield every matching query across all pages (default: created in the last 90 days)."""
        kwargs: dict[str, Any] = {"page_size": page_size}
        if processing_statuses:
            kwargs["processing_statuses"] = list(processing_statuses)
        if created_since:
            kwargs["created_since"] = _utc(created_since)
        if created_until:
            kwargs["created_until"] = _utc(created_until)
        while True:
            resp = call_with_retry(self.api.get_queries, **kwargs)
            yield from resp.queries or []
            token = resp.pagination.next_token if resp.pagination else None
            if not token:
                return
            kwargs["pagination_token"] = token  # other filters must be sent again unchanged

    def cancel_query(self, query_id: str) -> None:
        """Cancel a query that is still IN_QUEUE or IN_PROGRESS."""
        call_with_retry(self.api.cancel_query, query_id)

    def wait_for_query(
        self,
        query_id: str,
        poll_interval: float = 30.0,
        timeout: float = 60 * 60,
        on_status: Callable[[str], None] | None = None,
    ) -> Query:
        """Poll until the query is DONE. Raises QueryProcessingError on FATAL/CANCELLED.

        `on_status` is called with the processing status each time it changes.
        """
        deadline = time.monotonic() + timeout
        last_status = None
        while True:
            query = self.get_query(query_id)
            status = query.processing_status
            if on_status and status != last_status:
                on_status(status)
            last_status = status
            if status == QueryStatus.DONE:
                return query
            if status in QueryStatus.TERMINAL:
                raise QueryProcessingError(query_id, status, self._error_details(query))
            if time.monotonic() + poll_interval > deadline:
                raise ReportTimeoutError(f"Data Kiosk query {query_id} still {status} after {timeout:.0f}s")
            time.sleep(poll_interval)

    def _error_details(self, query: Query) -> str | None:
        if not query.error_document_id:
            return None
        try:
            return self.download_text(query.error_document_id)[:2000]
        except Exception:
            logger.exception("Could not fetch error document for Data Kiosk query %s", query.query_id)
            return None

    # ---------- Documents ----------

    def get_document(self, document_id: str) -> GetDocumentResponse:
        """Document metadata incl. a pre-signed URL that expires after 5 minutes."""
        return call_with_retry(self.api.get_document, document_id)

    def download_text(self, document_id: str) -> str:
        return download_text(document_id, self.get_document(document_id).document_url)

    def records(self, query: Query) -> list[dict[str, Any]]:
        """Records of one DONE query page. Empty when the query found no data (no dataDocumentId)."""
        if not query.data_document_id:
            return []
        return parse_jsonl(self.download_text(query.data_document_id))

    def all_records(
        self, done: Query, poll_interval: float = 30.0, on_page: Callable[[int], None] | None = None
    ) -> list[dict[str, Any]]:
        """Records of a DONE query and of every further page (each page is a new query). Blocking."""
        records = self.records(done)
        page = 1
        while done.pagination and done.pagination.next_token:
            page += 1
            if on_page:
                on_page(page)
            query_id = self.create_query(done.query, pagination_token=done.pagination.next_token)
            done = self.wait_for_query(query_id, poll_interval=poll_interval)
            records.extend(self.records(done))
        return records
