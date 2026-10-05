"""FBA Inventory API (v1) wrapper built on amzn-sp-api.

https://developer-docs.amazon/sp-api/reference/getinventorysummaries

Typical use:
    service = FbaInventoryService(AmazonCredentials.for_marketplace(Marketplace.UK))
    summaries = service.get_inventory_summaries(Marketplace.UK.marketplace_id)
"""

from datetime import datetime, timezone

from spapi import ApiClient
from spapi.api.fba_inventory_v1.fba_inventory_api import FbaInventoryApi
from spapi.models.fba_inventory_v1 import InventorySummary

from app.integration.amazon.client import build_api_client, call_with_retry
from app.integration.amazon.config import AmazonCredentials
from app.integration.amazon.exceptions import AmazonApiError


class FbaInventoryService:
    """One instance per seller account (credentials). Safe to reuse across calls."""

    def __init__(
        self,
        credentials: AmazonCredentials | None = None,
        api_client: ApiClient | None = None,
    ):
        self.credentials = credentials or AmazonCredentials.from_env()
        self._api_client = api_client
        self._api: FbaInventoryApi | None = None

    @property
    def api(self) -> FbaInventoryApi:
        # Built lazily: creating the SDK client performs an LWA token request.
        if self._api is None:
            self._api = FbaInventoryApi(self._api_client or build_api_client(self.credentials))
        return self._api

    def get_inventory_summaries(
        self,
        marketplace_id: str,
        details: bool = True,
        start_date_time: datetime | None = None,
    ) -> list[InventorySummary]:
        """Every FBA inventory summary for one marketplace, across all pages.

        Without start_date_time Amazon returns all summaries; with it, only those changed since then.
        Pages are fetched back to back because a nextToken expires 30 seconds after it is issued.
        """
        kwargs = {"details": details}
        if start_date_time:
            if start_date_time.tzinfo is None:
                start_date_time = start_date_time.replace(tzinfo=timezone.utc)
            kwargs["start_date_time"] = start_date_time

        summaries: list[InventorySummary] = []
        while True:
            resp = call_with_retry(
                self.api.get_inventory_summaries,
                "Marketplace",
                marketplace_id,
                [marketplace_id],
                **kwargs,
            )
            if resp.errors:
                raise AmazonApiError(
                    "SP-API getInventorySummaries returned errors: "
                    + "; ".join(f"{e.code}: {e.message}" for e in resp.errors)
                )
            summaries.extend((resp.payload and resp.payload.inventory_summaries) or [])
            next_token = resp.pagination and resp.pagination.next_token
            if not next_token:
                return summaries
            # Follow-up pages repeat the original parameters plus nextToken.
            kwargs["next_token"] = next_token
