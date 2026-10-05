from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AmazonMarketplace(Base):
    """A marketplace the seller sells in. The app's own record, kept apart from the raw integration
    tables (amazon_intg_*); orders and items reference it by id."""

    __tablename__ = "amazon_marketplaces"

    id: Mapped[int] = mapped_column(primary_key=True)
    # The integration row this marketplace came from; None when it is not (or no longer) in the integration data.
    integration_id: Mapped[int | None] = mapped_column(
        ForeignKey("amazon_intg_marketplace_participations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    region: Mapped[str] = mapped_column(String(2), index=True)  # NA | EU | FE
    # Amazon's marketplace id (e.g. ATVPDKIKX0DER); unique across all regions.
    marketplace_id: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    country_code: Mapped[str] = mapped_column(String(2))
    currency_code: Mapped[str] = mapped_column(String(3))
    language_code: Mapped[str] = mapped_column(String(10))
    domain_name: Mapped[str] = mapped_column(String(100))
    store_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    items: Mapped[list["AmazonItem"]] = relationship(back_populates="marketplace")  # noqa: F821
