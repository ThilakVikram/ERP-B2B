"""prefix amazon integration tables with amazon_intg_

Revision ID: 7b1f0c2e9a41
Revises: 3ac3468dacec
Create Date: 2026-09-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# A hand-made view (not a model) that reads order items; recreated to follow the rename.
VIEW = "available_sku_in_us"
VIEW_SQL = (
    "CREATE OR REPLACE SQL SECURITY DEFINER VIEW {view} AS "
    "SELECT DISTINCT sku FROM {table} WHERE marketplace_id = 'ATVPDKIKX0DER'"
)


def _recreate_view(table: str) -> None:
    exists = op.get_bind().execute(
        sa.text("SELECT COUNT(*) FROM information_schema.views WHERE table_schema = DATABASE() AND table_name = :v"),
        {"v": VIEW},
    ).scalar()
    if exists:
        op.execute(VIEW_SQL.format(view=VIEW, table=table))


# revision identifiers, used by Alembic.
revision: str = '7b1f0c2e9a41'
down_revision: Union[str, Sequence[str], None] = '3ac3468dacec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename every Amazon integration table (and its indexes) to amazon_intg_*."""
    # Views keep the old table name, so repoint available_sku_in_us afterwards.
    # RENAME TABLE only changes metadata: rows, foreign keys and data are kept.
    op.rename_table('amazon_reports', 'amazon_intg_reports')
    op.rename_table('fba_inventory_summaries', 'amazon_intg_fba_inventory_summaries')
    op.rename_table('marketplace_participations', 'amazon_intg_marketplace_participations')
    op.rename_table('merchant_listings', 'amazon_intg_merchant_listings')
    op.rename_table('order_report_items', 'amazon_intg_order_report_items')
    op.rename_table('sku_economics', 'amazon_intg_sku_economics')
    op.rename_table('sku_economics_fees', 'amazon_intg_sku_economics_fees')
    op.rename_table('sku_economics_ads', 'amazon_intg_sku_economics_ads')
    op.rename_table('sku_economics_costs', 'amazon_intg_sku_economics_costs')

    # Index / unique constraint names follow the table name.
    op.execute("ALTER TABLE amazon_intg_reports RENAME INDEX ix_amazon_reports_marketplace_id TO ix_amazon_intg_reports_marketplace_id")
    op.execute("ALTER TABLE amazon_intg_reports RENAME INDEX ix_amazon_reports_region TO ix_amazon_intg_reports_region")
    op.execute("ALTER TABLE amazon_intg_reports RENAME INDEX ix_amazon_reports_report_type TO ix_amazon_intg_reports_report_type")
    op.execute("ALTER TABLE amazon_intg_reports RENAME INDEX ix_amazon_reports_requested_by_id TO ix_amazon_intg_reports_requested_by_id")
    op.execute("ALTER TABLE amazon_intg_reports RENAME INDEX ix_amazon_reports_sync_status TO ix_amazon_intg_reports_sync_status")
    op.execute("ALTER TABLE amazon_intg_fba_inventory_summaries RENAME INDEX ix_fba_inventory_summaries_asin TO ix_amazon_intg_fba_inventory_summaries_asin")
    op.execute("ALTER TABLE amazon_intg_fba_inventory_summaries RENAME INDEX ix_fba_inventory_summaries_marketplace_id TO ix_amazon_intg_fba_inventory_summaries_marketplace_id")
    op.execute("ALTER TABLE amazon_intg_fba_inventory_summaries RENAME INDEX ix_fba_inventory_summaries_region TO ix_amazon_intg_fba_inventory_summaries_region")
    op.execute("ALTER TABLE amazon_intg_fba_inventory_summaries RENAME INDEX uq_fba_inventory_summaries_region_marketplace_sku TO uq_amazon_intg_fba_inventory_summaries_region_marketplace_sku")
    op.execute("ALTER TABLE amazon_intg_marketplace_participations RENAME INDEX ix_marketplace_participations_marketplace_id TO ix_amazon_intg_marketplace_participations_marketplace_id")
    op.execute("ALTER TABLE amazon_intg_marketplace_participations RENAME INDEX ix_marketplace_participations_region TO ix_amazon_intg_marketplace_participations_region")
    op.execute("ALTER TABLE amazon_intg_marketplace_participations RENAME INDEX uq_marketplace_participations_region_marketplace TO uq_amazon_intg_marketplace_participations_region_marketplace")
    op.execute("ALTER TABLE amazon_intg_merchant_listings RENAME INDEX ix_merchant_listings_amazon_report_id TO ix_amazon_intg_merchant_listings_amazon_report_id")
    op.execute("ALTER TABLE amazon_intg_merchant_listings RENAME INDEX ix_merchant_listings_asin TO ix_amazon_intg_merchant_listings_asin")
    op.execute("ALTER TABLE amazon_intg_merchant_listings RENAME INDEX ix_merchant_listings_marketplace_id TO ix_amazon_intg_merchant_listings_marketplace_id")
    op.execute("ALTER TABLE amazon_intg_merchant_listings RENAME INDEX ix_merchant_listings_region TO ix_amazon_intg_merchant_listings_region")
    op.execute("ALTER TABLE amazon_intg_merchant_listings RENAME INDEX uq_merchant_listings_region_marketplace_sku TO uq_amazon_intg_merchant_listings_region_marketplace_sku")
    op.execute("ALTER TABLE amazon_intg_order_report_items RENAME INDEX ix_order_report_items_amazon_order_id TO ix_amazon_intg_order_report_items_amazon_order_id")
    op.execute("ALTER TABLE amazon_intg_order_report_items RENAME INDEX ix_order_report_items_amazon_report_id TO ix_amazon_intg_order_report_items_amazon_report_id")
    op.execute("ALTER TABLE amazon_intg_order_report_items RENAME INDEX ix_order_report_items_asin TO ix_amazon_intg_order_report_items_asin")
    op.execute("ALTER TABLE amazon_intg_order_report_items RENAME INDEX ix_order_report_items_marketplace_id TO ix_amazon_intg_order_report_items_marketplace_id")
    op.execute("ALTER TABLE amazon_intg_order_report_items RENAME INDEX ix_order_report_items_region TO ix_amazon_intg_order_report_items_region")
    op.execute("ALTER TABLE amazon_intg_order_report_items RENAME INDEX uq_order_report_items_order_item TO uq_amazon_intg_order_report_items_order_item")
    op.execute("ALTER TABLE amazon_intg_sku_economics RENAME INDEX ix_sku_economics_amazon_report_id TO ix_amazon_intg_sku_economics_amazon_report_id")
    op.execute("ALTER TABLE amazon_intg_sku_economics RENAME INDEX ix_sku_economics_child_asin TO ix_amazon_intg_sku_economics_child_asin")
    op.execute("ALTER TABLE amazon_intg_sku_economics RENAME INDEX ix_sku_economics_marketplace_id TO ix_amazon_intg_sku_economics_marketplace_id")
    op.execute("ALTER TABLE amazon_intg_sku_economics RENAME INDEX ix_sku_economics_region TO ix_amazon_intg_sku_economics_region")
    op.execute("ALTER TABLE amazon_intg_sku_economics RENAME INDEX uq_sku_economics_marketplace_sku_period TO uq_amazon_intg_sku_economics_marketplace_sku_period")
    op.execute("ALTER TABLE amazon_intg_sku_economics_fees RENAME INDEX ix_sku_economics_fees_fee_type_name TO ix_amazon_intg_sku_economics_fees_fee_type_name")
    op.execute("ALTER TABLE amazon_intg_sku_economics_fees RENAME INDEX ix_sku_economics_fees_sku_economics_id TO ix_amazon_intg_sku_economics_fees_sku_economics_id")
    op.execute("ALTER TABLE amazon_intg_sku_economics_ads RENAME INDEX ix_sku_economics_ads_ad_type_name TO ix_amazon_intg_sku_economics_ads_ad_type_name")
    op.execute("ALTER TABLE amazon_intg_sku_economics_ads RENAME INDEX ix_sku_economics_ads_sku_economics_id TO ix_amazon_intg_sku_economics_ads_sku_economics_id")
    op.execute("ALTER TABLE amazon_intg_sku_economics_costs RENAME INDEX ix_sku_economics_costs_cost_type TO ix_amazon_intg_sku_economics_costs_cost_type")
    op.execute("ALTER TABLE amazon_intg_sku_economics_costs RENAME INDEX ix_sku_economics_costs_sku_economics_id TO ix_amazon_intg_sku_economics_costs_sku_economics_id")


    _recreate_view("amazon_intg_order_report_items")

def downgrade() -> None:
    """Back to the old table and index names."""
    op.execute("ALTER TABLE amazon_intg_reports RENAME INDEX ix_amazon_intg_reports_marketplace_id TO ix_amazon_reports_marketplace_id")
    op.execute("ALTER TABLE amazon_intg_reports RENAME INDEX ix_amazon_intg_reports_region TO ix_amazon_reports_region")
    op.execute("ALTER TABLE amazon_intg_reports RENAME INDEX ix_amazon_intg_reports_report_type TO ix_amazon_reports_report_type")
    op.execute("ALTER TABLE amazon_intg_reports RENAME INDEX ix_amazon_intg_reports_requested_by_id TO ix_amazon_reports_requested_by_id")
    op.execute("ALTER TABLE amazon_intg_reports RENAME INDEX ix_amazon_intg_reports_sync_status TO ix_amazon_reports_sync_status")
    op.execute("ALTER TABLE amazon_intg_fba_inventory_summaries RENAME INDEX ix_amazon_intg_fba_inventory_summaries_asin TO ix_fba_inventory_summaries_asin")
    op.execute("ALTER TABLE amazon_intg_fba_inventory_summaries RENAME INDEX ix_amazon_intg_fba_inventory_summaries_marketplace_id TO ix_fba_inventory_summaries_marketplace_id")
    op.execute("ALTER TABLE amazon_intg_fba_inventory_summaries RENAME INDEX ix_amazon_intg_fba_inventory_summaries_region TO ix_fba_inventory_summaries_region")
    op.execute("ALTER TABLE amazon_intg_fba_inventory_summaries RENAME INDEX uq_amazon_intg_fba_inventory_summaries_region_marketplace_sku TO uq_fba_inventory_summaries_region_marketplace_sku")
    op.execute("ALTER TABLE amazon_intg_marketplace_participations RENAME INDEX ix_amazon_intg_marketplace_participations_marketplace_id TO ix_marketplace_participations_marketplace_id")
    op.execute("ALTER TABLE amazon_intg_marketplace_participations RENAME INDEX ix_amazon_intg_marketplace_participations_region TO ix_marketplace_participations_region")
    op.execute("ALTER TABLE amazon_intg_marketplace_participations RENAME INDEX uq_amazon_intg_marketplace_participations_region_marketplace TO uq_marketplace_participations_region_marketplace")
    op.execute("ALTER TABLE amazon_intg_merchant_listings RENAME INDEX ix_amazon_intg_merchant_listings_amazon_report_id TO ix_merchant_listings_amazon_report_id")
    op.execute("ALTER TABLE amazon_intg_merchant_listings RENAME INDEX ix_amazon_intg_merchant_listings_asin TO ix_merchant_listings_asin")
    op.execute("ALTER TABLE amazon_intg_merchant_listings RENAME INDEX ix_amazon_intg_merchant_listings_marketplace_id TO ix_merchant_listings_marketplace_id")
    op.execute("ALTER TABLE amazon_intg_merchant_listings RENAME INDEX ix_amazon_intg_merchant_listings_region TO ix_merchant_listings_region")
    op.execute("ALTER TABLE amazon_intg_merchant_listings RENAME INDEX uq_amazon_intg_merchant_listings_region_marketplace_sku TO uq_merchant_listings_region_marketplace_sku")
    op.execute("ALTER TABLE amazon_intg_order_report_items RENAME INDEX ix_amazon_intg_order_report_items_amazon_order_id TO ix_order_report_items_amazon_order_id")
    op.execute("ALTER TABLE amazon_intg_order_report_items RENAME INDEX ix_amazon_intg_order_report_items_amazon_report_id TO ix_order_report_items_amazon_report_id")
    op.execute("ALTER TABLE amazon_intg_order_report_items RENAME INDEX ix_amazon_intg_order_report_items_asin TO ix_order_report_items_asin")
    op.execute("ALTER TABLE amazon_intg_order_report_items RENAME INDEX ix_amazon_intg_order_report_items_marketplace_id TO ix_order_report_items_marketplace_id")
    op.execute("ALTER TABLE amazon_intg_order_report_items RENAME INDEX ix_amazon_intg_order_report_items_region TO ix_order_report_items_region")
    op.execute("ALTER TABLE amazon_intg_order_report_items RENAME INDEX uq_amazon_intg_order_report_items_order_item TO uq_order_report_items_order_item")
    op.execute("ALTER TABLE amazon_intg_sku_economics RENAME INDEX ix_amazon_intg_sku_economics_amazon_report_id TO ix_sku_economics_amazon_report_id")
    op.execute("ALTER TABLE amazon_intg_sku_economics RENAME INDEX ix_amazon_intg_sku_economics_child_asin TO ix_sku_economics_child_asin")
    op.execute("ALTER TABLE amazon_intg_sku_economics RENAME INDEX ix_amazon_intg_sku_economics_marketplace_id TO ix_sku_economics_marketplace_id")
    op.execute("ALTER TABLE amazon_intg_sku_economics RENAME INDEX ix_amazon_intg_sku_economics_region TO ix_sku_economics_region")
    op.execute("ALTER TABLE amazon_intg_sku_economics RENAME INDEX uq_amazon_intg_sku_economics_marketplace_sku_period TO uq_sku_economics_marketplace_sku_period")
    op.execute("ALTER TABLE amazon_intg_sku_economics_fees RENAME INDEX ix_amazon_intg_sku_economics_fees_fee_type_name TO ix_sku_economics_fees_fee_type_name")
    op.execute("ALTER TABLE amazon_intg_sku_economics_fees RENAME INDEX ix_amazon_intg_sku_economics_fees_sku_economics_id TO ix_sku_economics_fees_sku_economics_id")
    op.execute("ALTER TABLE amazon_intg_sku_economics_ads RENAME INDEX ix_amazon_intg_sku_economics_ads_ad_type_name TO ix_sku_economics_ads_ad_type_name")
    op.execute("ALTER TABLE amazon_intg_sku_economics_ads RENAME INDEX ix_amazon_intg_sku_economics_ads_sku_economics_id TO ix_sku_economics_ads_sku_economics_id")
    op.execute("ALTER TABLE amazon_intg_sku_economics_costs RENAME INDEX ix_amazon_intg_sku_economics_costs_cost_type TO ix_sku_economics_costs_cost_type")
    op.execute("ALTER TABLE amazon_intg_sku_economics_costs RENAME INDEX ix_amazon_intg_sku_economics_costs_sku_economics_id TO ix_sku_economics_costs_sku_economics_id")

    op.rename_table('amazon_intg_sku_economics_costs', 'sku_economics_costs')
    op.rename_table('amazon_intg_sku_economics_ads', 'sku_economics_ads')
    op.rename_table('amazon_intg_sku_economics_fees', 'sku_economics_fees')
    op.rename_table('amazon_intg_sku_economics', 'sku_economics')
    op.rename_table('amazon_intg_order_report_items', 'order_report_items')
    op.rename_table('amazon_intg_merchant_listings', 'merchant_listings')
    op.rename_table('amazon_intg_marketplace_participations', 'marketplace_participations')
    op.rename_table('amazon_intg_fba_inventory_summaries', 'fba_inventory_summaries')
    op.rename_table('amazon_intg_reports', 'amazon_reports')

    _recreate_view("order_report_items")
