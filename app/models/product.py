from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import String, Text, DateTime, Numeric, CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.invoice_line import InvoiceLine


class Product(Base):
    """Product entity model representing goods or services."""
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("unit_price >= 0", name="chk_product_unit_price_positive"),
        CheckConstraint("vat_rate >= 0 AND vat_rate <= 100", name="chk_product_vat_rate_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    vat_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    invoice_lines: Mapped[List["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="product"
    )

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, code='{self.code}', name='{self.name}', price={self.unit_price})>"
