"""Order report types we support. Add a type here only together with its report module."""

from enum import Enum


class OrderReportType(str, Enum):
    GET_FLAT_FILE_ALL_ORDERS_DATA_BY_ORDER_DATE_GENERAL = "GET_FLAT_FILE_ALL_ORDERS_DATA_BY_ORDER_DATE_GENERAL"
