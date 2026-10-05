"""Sellers API (v1) wrapper built on amzn-sp-api.

https://developer-docs.amazon/sp-api/reference/sellers-v1

Typical use:
    service = SellersService(AmazonCredentials.from_env(Region.EU))
    participations = service.get_marketplace_participations()
"""

from spapi import ApiClient
from spapi.api.sellers_v1.sellers_api import SellersApi
from spapi.models.sellers_v1 import MarketplaceParticipation

from app.integration.amazon.client import build_api_client, call_with_retry
from app.integration.amazon.config import AmazonCredentials
from app.integration.amazon.exceptions import AmazonApiError


class SellersService:
    """One instance per seller account (credentials). Safe to reuse across calls."""

    def __init__(
        self,
        credentials: AmazonCredentials | None = None,
        api_client: ApiClient | None = None,
    ):
        self.credentials = credentials or AmazonCredentials.from_env()
        self._api_client = api_client
        self._api: SellersApi | None = None

    @property
    def api(self) -> SellersApi:
        # Built lazily: creating the SDK client performs an LWA token request.
        if self._api is None:
            self._api = SellersApi(self._api_client or build_api_client(self.credentials))
        return self._api

    def get_marketplace_participations(self) -> list[MarketplaceParticipation]:
        """Marketplaces the seller can sell in (for this region), with participation status."""
        resp = call_with_retry(self.api.get_marketplace_participations)
        if resp.errors:
            raise AmazonApiError(
                "SP-API getMarketplaceParticipations returned errors: "
                + "; ".join(f"{e.code}: {e.message}" for e in resp.errors)
            )
        return resp.payload or []
