"""Collects every v1 endpoint router. Register new feature routers here."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    amazon_items,
    amazon_marketplaces,
    auth,
    data_kiosk_economics,
    data_kiosk_queries,
    inventory,
    listing_reports,
    order_reports,
    reports,
    sellers,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(sellers.router)
api_router.include_router(inventory.router)
api_router.include_router(order_reports.router)
api_router.include_router(listing_reports.router)
api_router.include_router(data_kiosk_economics.router)
api_router.include_router(data_kiosk_queries.router)
api_router.include_router(reports.router)
api_router.include_router(amazon_marketplaces.router)
api_router.include_router(amazon_items.router)
