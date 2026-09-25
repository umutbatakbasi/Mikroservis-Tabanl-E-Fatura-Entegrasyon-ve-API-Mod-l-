from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import Numeric, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.invoice_header import InvoiceHeader
    from app.models.product import Product


class InvoiceLine(Base):
    """Invoice line item entity model."""
    __tablename__ = "invoice_lines"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_invoice_line_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="chk_invoice_line_unit_price_positive"),
        CheckConstraint("vat_rate >= 0 AND vat_rate <= 100", name="chk_invoice_line_vat_rate_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    invoice_id: Mapped[int] = mapped_column(
        ForeignKey("invoice_headers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    vat_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    vat_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # Relationships
    invoice: Mapped["InvoiceHeader"] = relationship("InvoiceHeader", back_populates="lines")
    product: Mapped["Product"] = relationship("Product", back_populates="invoice_lines", lazy="joined")

    def __repr__(self) -> str:
        return f"<InvoiceLine(id={self.id}, invoice_id={self.invoice_id}, product_id={self.product_id}, total={self.line_total})>"
