from decimal import Decimal
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.invoice_header import InvoiceHeader, InvoiceStatus
from app.models.invoice_line import InvoiceLine
from app.repositories.customer_repository import CustomerRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.invoice_repository import InvoiceRepository
from app.schemas.invoice import InvoiceCreate, InvoiceSendResponse
from app.services.einvoice_service import BaseEInvoiceService, MockEInvoiceService


class InvoiceService:
    """Service layer managing invoice calculations, validation, number generation, and e-invoice dispatch."""

    def __init__(
        self,
        invoice_repo: InvoiceRepository = InvoiceRepository(),
        customer_repo: CustomerRepository = CustomerRepository(),
        product_repo: ProductRepository = ProductRepository(),
        einvoice_service: BaseEInvoiceService = MockEInvoiceService(),
    ):
        self.invoice_repo = invoice_repo
        self.customer_repo = customer_repo
        self.product_repo = product_repo
        self.einvoice_service = einvoice_service

    def _generate_invoice_number(self, db: Session, year: int) -> str:
        """Generate sequential, collision-free invoice number format: INV-YYYY-000001."""
        prefix = f"{settings.INVOICE_NUMBER_PREFIX}-{year}"
        last_number = self.invoice_repo.get_last_invoice_number_for_prefix(db=db, prefix=prefix)

        if not last_number:
            seq = 1
        else:
            try:
                parts = last_number.split("-")
                seq = int(parts[-1]) + 1
            except (ValueError, IndexError):
                seq = 1

        new_number = f"{prefix}-{seq:06d}"
        # Safety check against collision
        while self.invoice_repo.get_by_invoice_number(db=db, invoice_number=new_number):
            seq += 1
            new_number = f"{prefix}-{seq:06d}"

        return new_number

    def get_all_invoices(self, db: Session, skip: int = 0, limit: int = 100) -> List[InvoiceHeader]:
        return self.invoice_repo.get_all(db=db, skip=skip, limit=limit)

    def get_invoice_by_id(self, db: Session, invoice_id: int) -> InvoiceHeader:
        invoice = self.invoice_repo.get_by_id(db=db, invoice_id=invoice_id)
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invoice with ID {invoice_id} not found."
            )
        return invoice

    def get_invoice_lines(self, db: Session, invoice_id: int) -> List[InvoiceLine]:
        # Validate invoice exists
        self.get_invoice_by_id(db=db, invoice_id=invoice_id)
        return self.invoice_repo.get_lines_by_invoice_id(db=db, invoice_id=invoice_id)

    def create_invoice(self, db: Session, invoice_in: InvoiceCreate) -> InvoiceHeader:
        """
        Create invoice with strict validations:
        1. Validate customer existence
        2. Validate each product existence
        3. Retrieve product prices from database (prevent client tampering)
        4. Calculate line_total, vat_amount, total_amount, total_vat, grand_total
        5. Generate sequential invoice number
        6. Persist within transactional boundary, rollback on failure
        """
        # 1. Customer verification
        customer = self.customer_repo.get_by_id(db=db, customer_id=invoice_in.customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with ID {invoice_in.customer_id} not found."
            )

        # 2. Product verification
        requested_product_ids = [line.product_id for line in invoice_in.lines]
        products = self.product_repo.get_by_ids(db=db, product_ids=list(set(requested_product_ids)))
        product_map = {p.id: p for p in products}

        for pid in requested_product_ids:
            if pid not in product_map:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product with ID {pid} not found."
                )

        try:
            # 3. Calculation & Line construction
            total_amount = Decimal("0.00")
            total_vat = Decimal("0.00")
            invoice_lines: List[InvoiceLine] = []

            for line_in in invoice_in.lines:
                product = product_map[line_in.product_id]
                quantity = Decimal(str(line_in.quantity))
                unit_price = Decimal(str(product.unit_price))
                vat_rate = Decimal(str(product.vat_rate))

                # line_total = quantity * unit_price
                line_total = (quantity * unit_price).quantize(Decimal("0.01"))
                # vat_amount = line_total * (vat_rate / 100)
                vat_amount = (line_total * (vat_rate / Decimal("100"))).quantize(Decimal("0.01"))

                total_amount += line_total
                total_vat += vat_amount

                invoice_line = InvoiceLine(
                    product_id=product.id,
                    quantity=quantity,
                    unit_price=unit_price,
                    vat_rate=vat_rate,
                    line_total=line_total,
                    vat_amount=vat_amount,
                )
                invoice_lines.append(invoice_line)

            grand_total = total_amount + total_vat

            # 4. Generate invoice number
            invoice_number = self._generate_invoice_number(db=db, year=invoice_in.invoice_date.year)

            # 5. Create header
            invoice = InvoiceHeader(
                invoice_number=invoice_number,
                customer_id=customer.id,
                invoice_date=invoice_in.invoice_date,
                total_amount=total_amount,
                total_vat=total_vat,
                grand_total=grand_total,
                status=InvoiceStatus.DRAFT.value,
                lines=invoice_lines,
            )

            created_invoice = self.invoice_repo.create(db=db, invoice=invoice)
            db.commit()
            return self.get_invoice_by_id(db=db, invoice_id=created_invoice.id)

        except Exception:
            db.rollback()
            raise

    def delete_invoice(self, db: Session, invoice_id: int) -> None:
        invoice = self.get_invoice_by_id(db=db, invoice_id=invoice_id)
        try:
            self.invoice_repo.delete(db=db, invoice=invoice)
            db.commit()
        except Exception:
            db.rollback()
            raise

    def send_invoice(
        self,
        db: Session,
        invoice_id: int,
        custom_einvoice_service: Optional[BaseEInvoiceService] = None,
    ) -> InvoiceSendResponse:
        """Transmit invoice via e-invoice provider and update status."""
        invoice = self.get_invoice_by_id(db=db, invoice_id=invoice_id)
        service = custom_einvoice_service or self.einvoice_service

        if invoice.status == InvoiceStatus.ACCEPTED.value:
            return InvoiceSendResponse(
                success=True,
                message="Fatura daha önce onaylanmış durumda.",
                invoice_id=invoice.id,
                invoice_number=invoice.invoice_number,
                uuid=invoice.uuid or "",
                status=invoice.status,
            )

        try:
            result = service.send_invoice(invoice=invoice)
            invoice.uuid = result.get("uuid")
            invoice.status = result.get("status", InvoiceStatus.SENT.value)
            self.invoice_repo.update(db=db, invoice=invoice)
            db.commit()

            return InvoiceSendResponse(
                success=result.get("success", True),
                message=result.get("message", "Fatura başarıyla gönderildi."),
                invoice_id=invoice.id,
                invoice_number=invoice.invoice_number,
                uuid=invoice.uuid or "",
                status=invoice.status,
            )
        except Exception:
            db.rollback()
            raise
