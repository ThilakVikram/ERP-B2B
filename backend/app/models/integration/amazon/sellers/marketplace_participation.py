from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MarketplaceParticipation(Base):
    """A marketplace the seller participates in, as returned by Sellers API v1 for one region."""

    __tablename__ = "amazon_intg_marketplace_participations"
    __table_args__ = (UniqueConstraint("region", "marketplace_id", name="uq_amazon_intg_marketplace_participations_region_marketplace"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    # The app marketplace created from this row (the other side of amazon_marketplaces.integration_id);
    # None until marketplaces are synced. use_alter: the two tables reference each other.
    amazon_marketplace_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "amazon_marketplaces.id",
            ondelete="SET NULL",
            use_alter=True,
            name="fk_amazon_intg_marketplace_participations_amazon_marketplace_id",
        ),
        nullable=True,
        index=True,
    )
    region: Mapped[str] = mapped_column(String(2), index=True)  # NA | EU | FE
    marketplace_id: Mapped[str] = mapped_column(String(20), index=True)
    name: Mapped[str] = mapped_column(String(100))
    country_code: Mapped[str] = mapped_column(String(2))
    default_currency_code: Mapped[str] = mapped_column(String(3))
    default_language_code: Mapped[str] = mapped_column(String(10))
    domain_name: Mapped[str] = mapped_column(String(100))
    store_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_participating: Mapped[bool] = mapped_column(Boolean, default=False)
    has_suspended_listings: Mapped[bool] = mapped_column(Boolean, default=False)
    last_synced_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
