from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

if TYPE_CHECKING:
    from app.models.lead_search import LeadSearch

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    cpf: Mapped[Optional[str]] = mapped_column(String(14))
    phone: Mapped[Optional[str]] = mapped_column(String(32))
    role: Mapped[str] = mapped_column(String(20), default="user")

    lead_searches: Mapped[list["LeadSearch"]] = relationship(
        "LeadSearch",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"

  

