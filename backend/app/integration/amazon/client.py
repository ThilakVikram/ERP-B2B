"""Builds amzn-sp-api clients and wraps SP-API calls with retry on throttling."""

import logging
import random
import time
from collections.abc import Callable
from typing import TypeVar

from spapi import ApiClient, ApiException, SPAPIClient, SPAPIConfig
from spapi.auth.lwa_exception import LwaException

from app.integration.amazon.config import AmazonCredentials
from app.integration.amazon.exceptions import AmazonApiError

logger = logging.getLogger(__name__)

T = TypeVar("T")

# 429 = throttled (QuotaExceeded); 5xx = transient Amazon-side failures
RETRYABLE_STATUSES = {429, 500, 502, 503, 504}


def build_api_client(credentials: AmazonCredentials) -> ApiClient:
    """Return an authenticated SDK ApiClient. Performs an LWA token exchange immediately."""
    sp_config = SPAPIConfig(
        client_id=credentials.client_id,
        client_secret=credentials.client_secret,
        refresh_token=credentials.refresh_token,
        region=credentials.region.value,
    )
    try:
        return SPAPIClient(sp_config, endpoint=credentials.endpoint).api_client
    except LwaException as exc:
        raise AmazonApiError(
            f"Amazon LWA token request failed for {credentials.region.value}: {_lwa_error(exc)}"
        ) from exc


def _lwa_error(exc: LwaException) -> str:
    """Amazon's error from the LWA response. The SDK drops it for 4xx (a 4xx Response is falsy)."""
    response = getattr(exc.__cause__, "response", None)
    if response is not None:
        try:
            body = response.json()
            return f"{body.get('error')}: {body.get('error_description')} (HTTP {response.status_code})"
        except ValueError:
            return f"HTTP {response.status_code}"
    return str(exc)


def call_with_retry(
    fn: Callable[..., T],
    *args,
    max_retries: int = 5,
    base_delay: float = 2.0,
    max_delay: float = 60.0,
    **kwargs,
) -> T:
    """Call an SDK operation, backing off exponentially on throttling / 5xx."""
    for attempt in range(max_retries + 1):
        try:
            return fn(*args, **kwargs)
        except ApiException as exc:
            if exc.status not in RETRYABLE_STATUSES or attempt == max_retries:
                raise AmazonApiError(
                    f"SP-API {getattr(fn, '__name__', 'call')} failed ({exc.status} {exc.reason})",
                    status=exc.status,
                    body=exc.body,
                ) from exc
            delay = min(max_delay, base_delay * 2**attempt) + random.uniform(0, 1)
            logger.warning(
                "SP-API %s returned %s, retrying in %.1fs (attempt %d/%d)",
                getattr(fn, "__name__", "call"), exc.status, delay, attempt + 1, max_retries,
            )
            time.sleep(delay)
    raise AssertionError("unreachable")
