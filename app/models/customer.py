from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.invoice_header import InvoiceHeader


class Customer(Base):
    """Customer entity model representing a commercial or individual client."""
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tax_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    invoices: Mapped[List["InvoiceHeader"]] = relationship(
        "InvoiceHeader",
        back_populates="customer",
        cascade="all, delete-orphan",
        order_by="desc(InvoiceHeader.created_at)"
    )

    def __repr__(self) -> str:
        return f"<Customer(id={self.id}, name='{self.name}', tax_number='{self.tax_number}')>"
