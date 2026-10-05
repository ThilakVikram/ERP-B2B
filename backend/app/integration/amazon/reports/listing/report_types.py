"""Listing (inventory) report types we support. Add a type here only together with its report module."""

from enum import Enum


class ListingReportType(str, Enum):
    GET_MERCHANT_LISTINGS_ALL_DATA = "GET_MERCHANT_LISTINGS_ALL_DATA"
