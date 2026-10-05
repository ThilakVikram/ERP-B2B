"""SP-API credentials. Per-region defaults come from env (app.config); pass explicit values per seller."""

from dataclasses import dataclass, field, replace

from app import config
from app.integration.amazon.exceptions import AmazonConfigError
from app.integration.amazon.marketplaces import Marketplace, Region

REGION_ENDPOINTS = {
    Region.NA: "https://sellingpartnerapi-na.amazon.com",
    Region.EU: "https://sellingpartnerapi-eu.amazon.com",
    Region.FE: "https://sellingpartnerapi-fe.amazon.com",
}
SANDBOX_REGION_ENDPOINTS = {
    Region.NA: "https://sandbox.sellingpartnerapi-na.amazon.com",
    Region.EU: "https://sandbox.sellingpartnerapi-eu.amazon.com",
    Region.FE: "https://sandbox.sellingpartnerapi-fe.amazon.com",
}


@dataclass(frozen=True)
class AmazonCredentials:
    """LWA app credentials plus one seller's refresh token for one region."""

    client_id: str
    client_secret: str
    refresh_token: str
    region: Region = Region.NA
    sandbox: bool = False
    marketplace_ids: tuple[str, ...] = field(default_factory=tuple)

    @property
    def endpoint(self) -> str:
        return (SANDBOX_REGION_ENDPOINTS if self.sandbox else REGION_ENDPOINTS)[self.region]

    @classmethod
    def from_env(cls, region: Region | str | None = None) -> "AmazonCredentials":
        """Credentials for one region from AMAZON_SP_API_<REGION>_* (default region if omitted)."""
        region_name = (region.value if isinstance(region, Region) else region or config.AMAZON_SP_API_DEFAULT_REGION).upper()
        try:
            region = Region(region_name)
        except ValueError:
            raise AmazonConfigError(f"SP-API region must be one of NA, EU, FE (got {region_name!r})")

        settings = config.AMAZON_SP_API_REGIONS[region.value]
        missing = [
            name
            for name, key in (
                ("AMAZON_SP_API_CLIENT_ID", "client_id"),
                ("AMAZON_SP_API_CLIENT_SECRET", "client_secret"),
                (f"AMAZON_SP_API_{region.value}_REFRESH_TOKEN", "refresh_token"),
            )
            if not settings[key]
        ]
        if missing:
            raise AmazonConfigError(f"Missing SP-API settings for {region.value}: {', '.join(missing)}")
        return cls(
            client_id=settings["client_id"],
            client_secret=settings["client_secret"],
            refresh_token=settings["refresh_token"],
            region=region,
            sandbox=config.AMAZON_SP_API_SANDBOX,
            marketplace_ids=tuple(settings["marketplace_ids"]),
        )

    @classmethod
    def for_marketplace(cls, marketplace: Marketplace) -> "AmazonCredentials":
        """Credentials of the marketplace's region, scoped to just that marketplace."""
        return replace(cls.from_env(marketplace.region), marketplace_ids=(marketplace.marketplace_id,))


def configured_regions() -> list[Region]:
    """Regions that have a refresh token set in env."""
    return [Region(r) for r, s in config.AMAZON_SP_API_REGIONS.items() if s["refresh_token"]]
