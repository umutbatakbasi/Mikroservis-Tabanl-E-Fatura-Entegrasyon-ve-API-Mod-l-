from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.invoice import (
    InvoiceCreate,
    InvoiceResponse,
    InvoiceLineResponse,
    InvoiceSendResponse,
)
from app.services.invoice_service import InvoiceService
from app.services.einvoice_service import get_einvoice_service, BaseEInvoiceService

router = APIRouter(prefix="/invoices", tags=["Invoices"])
invoice_service = InvoiceService()


@router.post(
    "",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yeni fatura oluştur",
    description=(
        "Fatura üst bilgisi ve kalemlerini oluşturur. Fatura toplamları müşteri ve ürün "
        "bilgileri veritabanından doğrulanarak backend tarafında otomatik hesaplanır."
    )
)
def create_invoice(
    invoice_in: InvoiceCreate,
    db: Session = Depends(get_db)
):
    return invoice_service.create_invoice(db=db, invoice_in=invoice_in)


@router.get(
    "",
    response_model=List[InvoiceResponse],
    status_code=status.HTTP_200_OK,
    summary="Faturaları listele",
    description="Sistemdeki tüm faturaları sayfalanmış olarak listeler."
)
def get_invoices(
    skip: int = Query(0, ge=0, description="Atlanacak kayıt sayısı"),
    limit: int = Query(100, ge=1, le=500, description="Döndürülecek maksimum kayıt sayısı"),
    db: Session = Depends(get_db)
):
    return invoice_service.get_all_invoices(db=db, skip=skip, limit=limit)


@router.get(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    status_code=status.HTTP_200_OK,
    summary="Fatura detayını getir",
    description="ID'si verilen faturanın müşteri ve kalem detaylarıyla birlikte tüm bilgilerini getirir."
)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db)
):
    return invoice_service.get_invoice_by_id(db=db, invoice_id=invoice_id)


@router.get(
    "/{invoice_id}/lines",
    response_model=List[InvoiceLineResponse],
    status_code=status.HTTP_200_OK,
    summary="Faturanın kalemlerini getir",
    description="ID'si verilen faturaya ait satır kalemlerini getirir."
)
def get_invoice_lines(
    invoice_id: int,
    db: Session = Depends(get_db)
):
    return invoice_service.get_invoice_lines(db=db, invoice_id=invoice_id)


@router.delete(
    "/{invoice_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Faturayı sil",
    description="ID'si verilen faturayı ve ilişkili kalemlerini sistemden siler."
)
def delete_invoice(
    invoice_id: int,
    db: Session = Depends(get_db)
):
    invoice_service.delete_invoice(db=db, invoice_id=invoice_id)
    return None


@router.post(
    "/{invoice_id}/send",
    response_model=InvoiceSendResponse,
    status_code=status.HTTP_200_OK,
    summary="Faturayı E-Fatura sistemine gönder",
    description="Faturayı E-Fatura entegratör servisine iletir, UUID atar ve durumunu günceller."
)
def send_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    einvoice_service: BaseEInvoiceService = Depends(get_einvoice_service)
):
    return invoice_service.send_invoice(
        db=db,
        invoice_id=invoice_id,
        custom_einvoice_service=einvoice_service
    )
