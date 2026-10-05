from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DataKioskQuery(Base):
    """One query in the Data Kiosk queue (Data Kiosk API 2023-11-15) and the outcome of storing its
    rows. Kept apart from amazon_intg_reports: Data Kiosk has its own queue and worker."""

    __tablename__ = "amazon_intg_data_kiosk_queries"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Amazon queryId; set once the queue worker has submitted the query.
    query_id: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    query_type: Mapped[str] = mapped_column(String(100), index=True)  # e.g. DATA_KIOSK_SKU_ECONOMICS
    region: Mapped[str] = mapped_column(String(2), index=True)  # NA | EU | FE
    marketplace_id: Mapped[str] = mapped_column(String(20), index=True)
    data_start_time: Mapped[datetime] = mapped_column(DateTime)
    data_end_time: Mapped[datetime] = mapped_column(DateTime)
    # Amazon's status: IN_QUEUE | IN_PROGRESS | DONE | FATAL | CANCELLED (None until submitted)
    processing_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # First result page's document; None when the query found no data.
    data_document_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Ours: QUEUED (waiting its turn) | PROCESSING | SYNCED | FAILED | CANCELLED
    sync_status: Mapped[str] = mapped_column(String(20), default="QUEUED", index=True)
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    inserted_count: Mapped[int] = mapped_column(Integer, default=0)
    skipped_count: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    requested_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
