from typing import List, Optional
from sqlalchemy import select, desc
from sqlalchemy.orm import Session, selectinload, joinedload
from app.models.invoice_header import InvoiceHeader
from app.models.invoice_line import InvoiceLine


class InvoiceRepository:
    """Repository handling database operations for Invoice Header and Line entities using SQLAlchemy 2.x."""

    @staticmethod
    def get_by_id(db: Session, invoice_id: int) -> Optional[InvoiceHeader]:
        stmt = (
            select(InvoiceHeader)
            .options(
                joinedload(InvoiceHeader.customer),
                selectinload(InvoiceHeader.lines).joinedload(InvoiceLine.product)
            )
            .where(InvoiceHeader.id == invoice_id)
        )
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_invoice_number(db: Session, invoice_number: str) -> Optional[InvoiceHeader]:
        stmt = (
            select(InvoiceHeader)
            .options(
                joinedload(InvoiceHeader.customer),
                selectinload(InvoiceHeader.lines).joinedload(InvoiceLine.product)
            )
            .where(InvoiceHeader.invoice_number == invoice_number)
        )
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[InvoiceHeader]:
        stmt = (
            select(InvoiceHeader)
            .options(
                joinedload(InvoiceHeader.customer),
                selectinload(InvoiceHeader.lines).joinedload(InvoiceLine.product)
            )
            .order_by(desc(InvoiceHeader.id))
            .offset(skip)
            .limit(limit)
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def get_last_invoice_number_for_prefix(db: Session, prefix: str) -> Optional[str]:
        """Find the latest invoice number matching a pattern like 'INV-2026-%'."""
        pattern = f"{prefix}-%"
        stmt = (
            select(InvoiceHeader.invoice_number)
            .where(InvoiceHeader.invoice_number.like(pattern))
            .order_by(desc(InvoiceHeader.id))
            .limit(1)
        )
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def create(db: Session, invoice: InvoiceHeader) -> InvoiceHeader:
        db.add(invoice)
        db.flush()
        db.refresh(invoice)
        return invoice

    @staticmethod
    def update(db: Session, invoice: InvoiceHeader) -> InvoiceHeader:
        db.flush()
        db.refresh(invoice)
        return invoice

    @staticmethod
    def delete(db: Session, invoice: InvoiceHeader) -> None:
        db.delete(invoice)
        db.flush()

    @staticmethod
    def get_lines_by_invoice_id(db: Session, invoice_id: int) -> List[InvoiceLine]:
        stmt = (
            select(InvoiceLine)
            .options(joinedload(InvoiceLine.product))
            .where(InvoiceLine.invoice_id == invoice_id)
            .order_by(InvoiceLine.id.asc())
        )
        return list(db.execute(stmt).scalars().all())
