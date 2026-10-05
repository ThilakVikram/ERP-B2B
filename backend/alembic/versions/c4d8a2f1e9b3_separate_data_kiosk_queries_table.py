"""separate data kiosk queries table

Data Kiosk queries move out of amazon_intg_reports into their own table (they have their own queue).
Existing queries are moved with their ids, so amazon_intg_sku_economics keeps pointing at the same
query, now through data_kiosk_query_id.

Revision ID: c4d8a2f1e9b3
Revises: 6d12c37db683
Create Date: 2026-09-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c4d8a2f1e9b3'
down_revision: Union[str, Sequence[str], None] = '6d12c37db683'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "amazon_intg_data_kiosk_queries"
REPORTS = "amazon_intg_reports"
SKU = "amazon_intg_sku_economics"
QUERY_TYPES = "('DATA_KIOSK_SKU_ECONOMICS')"

# Columns in both tables, as (queries column, reports column).
COLUMNS = [
    ("id", "id"),
    ("query_id", "report_id"),
    ("query_type", "report_type"),
    ("region", "region"),
    ("marketplace_id", "marketplace_id"),
    ("data_start_time", "data_start_time"),
    ("data_end_time", "data_end_time"),
    ("processing_status", "processing_status"),
    ("data_document_id", "report_document_id"),
    ("sync_status", "sync_status"),
    ("row_count", "row_count"),
    ("inserted_count", "inserted_count"),
    ("skipped_count", "skipped_count"),
    ("error", "error"),
    ("requested_by_id", "requested_by_id"),
    ("started_at", "started_at"),
    ("completed_at", "completed_at"),
    ("created_at", "created_at"),
    ("updated_at", "updated_at"),
]


def _foreign_key_name(table: str, column: str) -> str:
    """MySQL named these foreign keys itself (e.g. sku_economics_ibfk_1), so look the name up."""
    return op.get_bind().execute(
        sa.text(
            "SELECT constraint_name FROM information_schema.key_column_usage "
            "WHERE table_schema = DATABASE() AND table_name = :t AND column_name = :c "
            "AND referenced_table_name IS NOT NULL"
        ),
        {"t": table, "c": column},
    ).scalar_one()


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(TABLE,
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('query_id', sa.String(length=50), nullable=True),
    sa.Column('query_type', sa.String(length=100), nullable=False),
    sa.Column('region', sa.String(length=2), nullable=False),
    sa.Column('marketplace_id', sa.String(length=20), nullable=False),
    sa.Column('data_start_time', sa.DateTime(), nullable=False),
    sa.Column('data_end_time', sa.DateTime(), nullable=False),
    sa.Column('processing_status', sa.String(length=20), nullable=True),
    sa.Column('data_document_id', sa.String(length=255), nullable=True),
    sa.Column('sync_status', sa.String(length=20), nullable=False),
    sa.Column('row_count', sa.Integer(), nullable=False),
    sa.Column('inserted_count', sa.Integer(), nullable=False),
    sa.Column('skipped_count', sa.Integer(), nullable=False),
    sa.Column('error', sa.Text(), nullable=True),
    sa.Column('requested_by_id', sa.Integer(), nullable=True),
    sa.Column('started_at', sa.DateTime(), nullable=True),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['requested_by_id'], ['users.id'], name='fk_amazon_intg_data_kiosk_queries_requested_by_id_users'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('query_id')
    )
    op.create_index(op.f('ix_amazon_intg_data_kiosk_queries_marketplace_id'), TABLE, ['marketplace_id'], unique=False)
    op.create_index(op.f('ix_amazon_intg_data_kiosk_queries_query_type'), TABLE, ['query_type'], unique=False)
    op.create_index(op.f('ix_amazon_intg_data_kiosk_queries_region'), TABLE, ['region'], unique=False)
    op.create_index(op.f('ix_amazon_intg_data_kiosk_queries_requested_by_id'), TABLE, ['requested_by_id'], unique=False)
    op.create_index(op.f('ix_amazon_intg_data_kiosk_queries_sync_status'), TABLE, ['sync_status'], unique=False)

    # Move the Data Kiosk queries, keeping their ids.
    new_cols = ", ".join(q for q, _ in COLUMNS)
    old_cols = ", ".join(r for _, r in COLUMNS)
    op.execute(f"INSERT INTO {TABLE} ({new_cols}) SELECT {old_cols} FROM {REPORTS} WHERE report_type IN {QUERY_TYPES}")

    # SKU economics rows point at the moved query.
    op.add_column(SKU, sa.Column('data_kiosk_query_id', sa.Integer(), nullable=True))
    op.execute(f"UPDATE {SKU} SET data_kiosk_query_id = amazon_report_id")
    op.alter_column(SKU, 'data_kiosk_query_id', existing_type=sa.Integer(), nullable=False)
    op.drop_constraint(_foreign_key_name(SKU, 'amazon_report_id'), SKU, type_='foreignkey')
    op.drop_index('ix_amazon_intg_sku_economics_amazon_report_id', table_name=SKU)
    op.drop_column(SKU, 'amazon_report_id')
    op.create_index(op.f('ix_amazon_intg_sku_economics_data_kiosk_query_id'), SKU, ['data_kiosk_query_id'], unique=False)
    op.create_foreign_key(
        'fk_amazon_intg_sku_economics_data_kiosk_query_id', SKU, TABLE, ['data_kiosk_query_id'], ['id']
    )

    op.execute(f"DELETE FROM {REPORTS} WHERE report_type IN {QUERY_TYPES}")


def downgrade() -> None:
    """Downgrade schema."""
    # Reports created since the upgrade may have taken the queries' ids: move them back above every report id.
    offset = op.get_bind().execute(sa.text(f"SELECT COALESCE(MAX(id), 0) FROM {REPORTS}")).scalar_one()
    old_cols = ", ".join(r for _, r in COLUMNS)
    new_cols = ", ".join(f"id + {int(offset)}" if q == "id" else q for q, _ in COLUMNS)
    op.execute(f"INSERT INTO {REPORTS} ({old_cols}) SELECT {new_cols} FROM {TABLE}")

    op.add_column(SKU, sa.Column('amazon_report_id', sa.Integer(), nullable=True))
    op.execute(f"UPDATE {SKU} SET amazon_report_id = data_kiosk_query_id + {int(offset)}")
    op.alter_column(SKU, 'amazon_report_id', existing_type=sa.Integer(), nullable=False)
    op.drop_constraint('fk_amazon_intg_sku_economics_data_kiosk_query_id', SKU, type_='foreignkey')
    op.drop_index(op.f('ix_amazon_intg_sku_economics_data_kiosk_query_id'), table_name=SKU)
    op.drop_column(SKU, 'data_kiosk_query_id')
    op.create_index('ix_amazon_intg_sku_economics_amazon_report_id', SKU, ['amazon_report_id'], unique=False)
    op.create_foreign_key(None, SKU, REPORTS, ['amazon_report_id'], ['id'])

    op.drop_table(TABLE)
