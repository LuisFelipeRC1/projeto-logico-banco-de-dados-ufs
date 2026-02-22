from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey, UniqueConstraint, Column,JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

if TYPE_CHECKING:
    from app.models.lead_search import LeadSearch

class LeadResult(Base):
    __tablename__ = "lead_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 👇 ESTA linha é a que o erro está reclamando que falta/carece
    search_id: Mapped[int] = mapped_column(
        ForeignKey("lead_searches.id", ondelete="CASCADE"),  # <— nome da tabela TEM que ser "lead_searches"
        index=True,
    )
    website = Column(String(512), nullable=True)
    opening_hours = Column(JSON, nullable=True)  
    place_name: Mapped[Optional[str]] = mapped_column(String(255))
    address: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(64))
    rating: Mapped[Optional[float]] = mapped_column(Float)
    reviews_count: Mapped[Optional[int]] = mapped_column(Integer)
    url: Mapped[Optional[str]] = mapped_column(String(1024))
    source_id: Mapped[Optional[str]] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    search: Mapped["LeadSearch"] = relationship("LeadSearch", back_populates="results")

    __table_args__ = (
        UniqueConstraint("search_id", "source_id", name="uq_search_source"),
        # ou: UniqueConstraint("search_id", "url", name="uq_search_url"),
    )
    def __repr__(self) -> str:
        return f"<LeadResult id={self.id} place_name={self.place_name!r} search_id={self.search_id}>"