"""Database access for the DataKioskQuery model (the Data Kiosk queue). No business logic here."""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy import update as sql_update
from sqlalchemy.orm import Session

from app.models.integration.amazon.data_kiosk.data_kiosk_query import DataKioskQuery


def create(db: Session, **fields) -> DataKioskQuery:
    query = DataKioskQuery(**fields)
    db.add(query)
    db.commit()
    db.refresh(query)
    return query


def get(db: Session, query_pk: int) -> DataKioskQuery | None:
    return db.get(DataKioskQuery, query_pk)


def update(db: Session, query: DataKioskQuery, **fields) -> DataKioskQuery:
    for key, value in fields.items():
        setattr(query, key, value)
    db.commit()
    db.refresh(query)
    return query


def list_all(
    db: Session,
    region: str | None = None,
    marketplace_id: str | None = None,
    query_type: str | list[str] | None = None,
    limit: int = 100,
    sync_statuses: list[str] | None = None,
) -> list[DataKioskQuery]:
    """Newest first. query_type can be one type or a list (any of them)."""
    stmt = select(DataKioskQuery).order_by(DataKioskQuery.id.desc()).limit(limit)
    if sync_statuses:
        stmt = stmt.where(DataKioskQuery.sync_status.in_(sync_statuses))
    if region:
        stmt = stmt.where(DataKioskQuery.region == region)
    if marketplace_id:
        stmt = stmt.where(DataKioskQuery.marketplace_id == marketplace_id)
    if query_type:
        types = [query_type] if isinstance(query_type, str) else query_type
        stmt = stmt.where(DataKioskQuery.query_type.in_(types))
    return list(db.scalars(stmt))


def list_by_sync_status(db: Session, sync_statuses: list[str]) -> list[DataKioskQuery]:
    """Oldest first, i.e. queue order."""
    stmt = select(DataKioskQuery).where(DataKioskQuery.sync_status.in_(sync_statuses)).order_by(DataKioskQuery.id)
    return list(db.scalars(stmt))


def next_queued(db: Session, queued_status: str) -> DataKioskQuery | None:
    stmt = select(DataKioskQuery).where(DataKioskQuery.sync_status == queued_status).order_by(DataKioskQuery.id).limit(1)
    return db.scalars(stmt).first()


def find_active_duplicate(
    db: Session,
    active_statuses: list[str],
    query_type: str,
    marketplace_id: str,
    data_start_time: datetime,
    data_end_time: datetime,
) -> DataKioskQuery | None:
    stmt = (
        select(DataKioskQuery)
        .where(
            DataKioskQuery.sync_status.in_(active_statuses),
            DataKioskQuery.query_type == query_type,
            DataKioskQuery.marketplace_id == marketplace_id,
            DataKioskQuery.data_start_time == data_start_time,
            DataKioskQuery.data_end_time == data_end_time,
        )
        .limit(1)
    )
    return db.scalars(stmt).first()


def count_queued_before(db: Session, queued_status: str, query_pk: int) -> int:
    stmt = select(func.count()).where(DataKioskQuery.sync_status == queued_status, DataKioskQuery.id < query_pk)
    return db.scalar(stmt) or 0


def set_sync_status(db: Session, from_statuses: list[str], to_status: str) -> int:
    """Bulk status change; returns rows affected."""
    result = db.execute(
        sql_update(DataKioskQuery).where(DataKioskQuery.sync_status.in_(from_statuses)).values(sync_status=to_status)
    )
    db.commit()
    return result.rowcount


def count_by_sync_status(db: Session) -> dict[str, int]:
    stmt = select(DataKioskQuery.sync_status, func.count()).group_by(DataKioskQuery.sync_status)
    return {status: count for status, count in db.execute(stmt)}


def list_periods(
    db: Session, query_type: str, marketplace_id: str, sync_statuses: list[str]
) -> list[tuple[datetime, datetime, str]]:
    """(data_start_time, data_end_time, sync_status) of every matching request, oldest first."""
    stmt = (
        select(DataKioskQuery.data_start_time, DataKioskQuery.data_end_time, DataKioskQuery.sync_status)
        .where(
            DataKioskQuery.query_type == query_type,
            DataKioskQuery.marketplace_id == marketplace_id,
            DataKioskQuery.sync_status.in_(sync_statuses),
        )
        .order_by(DataKioskQuery.data_start_time)
    )
    return [tuple(row) for row in db.execute(stmt)]
