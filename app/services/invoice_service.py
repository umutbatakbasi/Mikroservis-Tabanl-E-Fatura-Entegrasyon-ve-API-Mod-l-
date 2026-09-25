from datetime import date
from decimal import Decimal
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.core.config import settings
from app.models.invoice_header import InvoiceHeader, InvoiceStatus
from app.models.invoice_line import InvoiceLine
from app.repositories.customer_repository import CustomerRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.invoice_repository import InvoiceRepository
from app.schemas.invoice import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceSendResponse,
    InvoiceUBLExportResponse,
)
from app.services.einvoice_service import BaseEInvoiceService, MockEInvoiceService
from app.services.ubl_service import ubl_service


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

    def get_all_invoices(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        customer_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        search: Optional[str] = None,
    ) -> List[InvoiceHeader]:
        """Fetch invoices with optional filtering for 3rd-party accounting and e-invoice integrators."""
        return self.invoice_repo.get_all(
            db=db,
            skip=skip,
            limit=limit,
            status=status,
            customer_id=customer_id,
            start_date=start_date,
            end_date=end_date,
            search=search,
        )

    def get_invoice_by_id(self, db: Session, invoice_id: int) -> InvoiceHeader:
        invoice = self.invoice_repo.get_by_id(db=db, invoice_id=invoice_id)
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Fatura bulunamadı (ID: {invoice_id})."
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
                detail=f"Müşteri bulunamadı (ID: {invoice_in.customer_id})."
            )

        # 2. Product verification
        requested_product_ids = [line.product_id for line in invoice_in.lines]
        products = self.product_repo.get_by_ids(db=db, product_ids=list(set(requested_product_ids)))
        product_map = {p.id: p for p in products}

        for pid in requested_product_ids:
            if pid not in product_map:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Ürün bulunamadı (ID: {pid})."
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

                line_total = (quantity * unit_price).quantize(Decimal("0.01"))
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

        except HTTPException:
            db.rollback()
            raise
        except SQLAlchemyError as err:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Veritabanı işleminde hata oluştu: {str(err)}"
            )
        except Exception:
            db.rollback()
            raise

    def update_invoice(self, db: Session, invoice_id: int, invoice_in: InvoiceUpdate) -> InvoiceHeader:
        """
        Update an existing invoice:
        - Only permitted if status is 'DRAFT'.
        - If lines are updated, recalculates totals from current product catalog.
        - Preserves transaction integrity.
        """
        invoice = self.get_invoice_by_id(db=db, invoice_id=invoice_id)

        if invoice.status != InvoiceStatus.DRAFT.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Fatura durumu '{invoice.status}' olduğu için güncellenemez. Yalnızca taslak (DRAFT) faturalar düzenlenebilir."
            )

        try:
            if invoice_in.customer_id is not None and invoice_in.customer_id != invoice.customer_id:
                customer = self.customer_repo.get_by_id(db=db, customer_id=invoice_in.customer_id)
                if not customer:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Müşteri bulunamadı (ID: {invoice_in.customer_id})."
                    )
                invoice.customer_id = customer.id

            if invoice_in.invoice_date is not None:
                invoice.invoice_date = invoice_in.invoice_date

            if invoice_in.lines is not None:
                # Validate products
                requested_pids = [l.product_id for l in invoice_in.lines]
                products = self.product_repo.get_by_ids(db=db, product_ids=list(set(requested_pids)))
                product_map = {p.id: p for p in products}

                for pid in requested_pids:
                    if pid not in product_map:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Ürün bulunamadı (ID: {pid})."
                        )

                # Clear old lines and calculate new lines
                invoice.lines.clear()
                total_amount = Decimal("0.00")
                total_vat = Decimal("0.00")

                for line_in in invoice_in.lines:
                    prod = product_map[line_in.product_id]
                    qty = Decimal(str(line_in.quantity))
                    price = Decimal(str(prod.unit_price))
                    rate = Decimal(str(prod.vat_rate))

                    line_total = (qty * price).quantize(Decimal("0.01"))
                    vat_amount = (line_total * (rate / Decimal("100"))).quantize(Decimal("0.01"))

                    total_amount += line_total
                    total_vat += vat_amount

                    invoice.lines.append(
                        InvoiceLine(
                            product_id=prod.id,
                            quantity=qty,
                            unit_price=price,
                            vat_rate=rate,
                            line_total=line_total,
                            vat_amount=vat_amount,
                        )
                    )

                invoice.total_amount = total_amount
                invoice.total_vat = total_vat
                invoice.grand_total = total_amount + total_vat

            self.invoice_repo.update(db=db, invoice=invoice)
            db.commit()
            return self.get_invoice_by_id(db=db, invoice_id=invoice.id)

        except HTTPException:
            db.rollback()
            raise
        except SQLAlchemyError as err:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Fatura güncelleme sırasında veritabanı hatası: {str(err)}"
            )
        except Exception:
            db.rollback()
            raise

    def delete_invoice(self, db: Session, invoice_id: int) -> None:
        invoice = self.get_invoice_by_id(db=db, invoice_id=invoice_id)
        try:
            self.invoice_repo.delete(db=db, invoice=invoice)
            db.commit()
        except SQLAlchemyError as err:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Fatura silinirken veritabanı hatası: {str(err)}"
            )
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
        except SQLAlchemyError as err:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Fatura gönderim durumunu güncellerken hata: {str(err)}"
            )
        except Exception:
            db.rollback()
            raise

    def export_invoice_ubl(self, db: Session, invoice_id: int) -> InvoiceUBLExportResponse:
        """
        Generate UBL-TR 1.2 XML compliant data structure for 3rd-party E-Invoice integrators.
        """
        invoice = self.get_invoice_by_id(db=db, invoice_id=invoice_id)
        cust = invoice.customer
        xml_content = ubl_service.generate_ubl_xml(invoice=invoice)

        return InvoiceUBLExportResponse(
            invoice_id=invoice.id,
            invoice_number=invoice.invoice_number,
            uuid=invoice.uuid,
            issue_date=invoice.invoice_date,
            profile_id="TICARIFATURA",
            invoice_type_code="SATIS",
            document_currency_code="TRY",
            customer_tax_number=cust.tax_number if cust else "",
            customer_name=cust.name if cust else "",
            total_amount=invoice.total_amount,
            total_vat=invoice.total_vat,
            grand_total=invoice.grand_total,
            ubl_xml=xml_content,
        )

    def get_invoice_xml_document(self, db: Session, invoice_id: int) -> str:
        """
        Generate raw UBL-TR 1.2 XML document string for application/xml HTTP responses.
        """
        invoice = self.get_invoice_by_id(db=db, invoice_id=invoice_id)
        return ubl_service.generate_ubl_xml(invoice=invoice)

