"""Database access for the AmazonReport model. No business logic here."""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy import update as sql_update
from sqlalchemy.orm import Session

from app.models.integration.amazon.reports.amazon_report import AmazonReport


def create(db: Session, **fields) -> AmazonReport:
    report = AmazonReport(**fields)
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def get(db: Session, report_pk: int) -> AmazonReport | None:
    return db.get(AmazonReport, report_pk)


def update(db: Session, report: AmazonReport, **fields) -> AmazonReport:
    for key, value in fields.items():
        setattr(report, key, value)
    db.commit()
    db.refresh(report)
    return report


def list_all(
    db: Session,
    region: str | None = None,
    marketplace_id: str | None = None,
    report_type: str | list[str] | None = None,
    limit: int = 100,
    sync_statuses: list[str] | None = None,
) -> list[AmazonReport]:
    """Newest first. report_type can be one type or a list (any of them)."""
    stmt = select(AmazonReport).order_by(AmazonReport.id.desc()).limit(limit)
    if sync_statuses:
        stmt = stmt.where(AmazonReport.sync_status.in_(sync_statuses))
    if region:
        stmt = stmt.where(AmazonReport.region == region)
    if marketplace_id:
        stmt = stmt.where(AmazonReport.marketplace_id == marketplace_id)
    if report_type:
        types = [report_type] if isinstance(report_type, str) else report_type
        stmt = stmt.where(AmazonReport.report_type.in_(types))
    return list(db.scalars(stmt))



def list_by_sync_status(db: Session, sync_statuses: list[str]) -> list[AmazonReport]:
    """Oldest first, i.e. queue order."""
    stmt = select(AmazonReport).where(AmazonReport.sync_status.in_(sync_statuses)).order_by(AmazonReport.id)
    return list(db.scalars(stmt))


def next_queued(db: Session, queued_status: str) -> AmazonReport | None:
    stmt = select(AmazonReport).where(AmazonReport.sync_status == queued_status).order_by(AmazonReport.id).limit(1)
    return db.scalars(stmt).first()


def find_active_duplicate(
    db: Session,
    active_statuses: list[str],
    report_type: str,
    marketplace_id: str,
    data_start_time: datetime,
    data_end_time: datetime,
) -> AmazonReport | None:
    stmt = (
        select(AmazonReport)
        .where(
            AmazonReport.sync_status.in_(active_statuses),
            AmazonReport.report_type == report_type,
            AmazonReport.marketplace_id == marketplace_id,
            AmazonReport.data_start_time == data_start_time,
            AmazonReport.data_end_time == data_end_time,
        )
        .limit(1)
    )
    return db.scalars(stmt).first()


def count_queued_before(db: Session, queued_status: str, report_pk: int) -> int:
    stmt = select(func.count()).where(AmazonReport.sync_status == queued_status, AmazonReport.id < report_pk)
    return db.scalar(stmt) or 0


def set_sync_status(db: Session, from_statuses: list[str], to_status: str) -> int:
    """Bulk status change; returns rows affected."""
    result = db.execute(
        sql_update(AmazonReport).where(AmazonReport.sync_status.in_(from_statuses)).values(sync_status=to_status)
    )
    db.commit()
    return result.rowcount


def count_by_sync_status(db: Session) -> dict[str, int]:
    stmt = select(AmazonReport.sync_status, func.count()).group_by(AmazonReport.sync_status)
    return {status: count for status, count in db.execute(stmt)}


def list_periods(
    db: Session, report_type: str, marketplace_id: str, sync_statuses: list[str]
) -> list[tuple[datetime, datetime, str]]:
    """(data_start_time, data_end_time, sync_status) of every matching request, oldest first."""
    stmt = (
        select(AmazonReport.data_start_time, AmazonReport.data_end_time, AmazonReport.sync_status)
        .where(
            AmazonReport.report_type == report_type,
            AmazonReport.marketplace_id == marketplace_id,
            AmazonReport.sync_status.in_(sync_statuses),
        )
        .order_by(AmazonReport.data_start_time)
    )
    return [tuple(row) for row in db.execute(stmt)]
