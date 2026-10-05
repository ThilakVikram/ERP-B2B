from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AmazonReport(Base):
    """One report request in the report queue (Reports API 2021-06-30) and the outcome of storing its rows."""

    __tablename__ = "amazon_intg_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Amazon reportId; set once the queue worker has asked Amazon for the report.
    report_id: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    report_type: Mapped[str] = mapped_column(String(100), index=True)
    region: Mapped[str] = mapped_column(String(2), index=True)  # NA | EU | FE
    marketplace_id: Mapped[str] = mapped_column(String(20), index=True)
    data_start_time: Mapped[datetime] = mapped_column(DateTime)
    data_end_time: Mapped[datetime] = mapped_column(DateTime)
    # Amazon's status: IN_QUEUE | IN_PROGRESS | DONE | FATAL | CANCELLED (None until requested)
    processing_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    report_document_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Ours: QUEUED (waiting its turn) | PROCESSING | SYNCED | FAILED | CANCELLED
    sync_status: Mapped[str] = mapped_column(String(20), default="QUEUED", index=True)
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    inserted_count: Mapped[int] = mapped_column(Integer, default=0)
    skipped_count: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    report_options: Mapped[dict | None] = mapped_column(JSON(none_as_null=True), nullable=True)
    requested_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
