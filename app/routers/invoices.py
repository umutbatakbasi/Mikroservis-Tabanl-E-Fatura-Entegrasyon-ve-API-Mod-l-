from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.invoice import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceResponse,
    InvoiceLineResponse,
    InvoiceSendResponse,
    InvoiceUBLExportResponse,
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
async def create_invoice(
    invoice_in: InvoiceCreate,
    db: Session = Depends(get_db)
):
    """Asenkron fatura oluşturma uç noktası."""
    return invoice_service.create_invoice(db=db, invoice_in=invoice_in)


@router.get(
    "",
    response_model=List[InvoiceResponse],
    status_code=status.HTTP_200_OK,
    summary="Faturaları listele / filtrele",
    description=(
        "Sistemdeki tüm faturaları üçüncü parti e-fatura entegratörleri ve ERP sistemleri "
        "için durum, tarih aralığı, müşteri ve arama kriterlerine göre asenkron olarak listeler."
    )
)
async def get_invoices(
    skip: int = Query(0, ge=0, description="Atlanacak kayıt sayısı"),
    limit: int = Query(100, ge=1, le=500, description="Döndürülecek maksimum kayıt sayısı"),
    status: Optional[str] = Query(None, description="Fatura durumu filtresi (DRAFT, SENT, ACCEPTED, REJECTED)"),
    customer_id: Optional[int] = Query(None, description="Belirli bir müşteriye ait faturaları filtrele"),
    start_date: Optional[date] = Query(None, description="Başlangıç fatura tarihi (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Bitiş fatura tarihi (YYYY-MM-DD)"),
    search: Optional[str] = Query(None, description="Fatura numarası veya müşteri adına göre arama"),
    db: Session = Depends(get_db)
):
    """Asenkron fatura sorgulama ve filtreleme uç noktası."""
    return invoice_service.get_all_invoices(
        db=db,
        skip=skip,
        limit=limit,
        status=status,
        customer_id=customer_id,
        start_date=start_date,
        end_date=end_date,
        search=search,
    )


@router.get(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    status_code=status.HTTP_200_OK,
    summary="Fatura detayını getir",
    description="ID'si verilen faturanın müşteri ve kalem detaylarıyla birlikte tüm bilgilerini getirir."
)
async def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db)
):
    return invoice_service.get_invoice_by_id(db=db, invoice_id=invoice_id)


@router.put(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    status_code=status.HTTP_200_OK,
    summary="Taslak faturayı güncelle",
    description=(
        "Yalnızca DRAFT (Taslak) durumundaki faturaların bilgilerini veya kalemlerini günceller. "
        "Gönderilmiş (SENT) veya onaylanmış (ACCEPTED) faturaların değiştirilmesini engeller."
    )
)
async def update_invoice(
    invoice_id: int,
    invoice_in: InvoiceUpdate,
    db: Session = Depends(get_db)
):
    return invoice_service.update_invoice(db=db, invoice_id=invoice_id, invoice_in=invoice_in)


@router.get(
    "/{invoice_id}/lines",
    response_model=List[InvoiceLineResponse],
    status_code=status.HTTP_200_OK,
    summary="Faturanın kalemlerini getir",
    description="ID'si verilen faturaya ait satır kalemlerini getirir."
)
async def get_invoice_lines(
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
async def delete_invoice(
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
async def send_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    einvoice_service: BaseEInvoiceService = Depends(get_einvoice_service)
):
    return invoice_service.send_invoice(
        db=db,
        invoice_id=invoice_id,
        custom_einvoice_service=einvoice_service
    )


@router.get(
    "/{invoice_id}/ubl",
    response_model=InvoiceUBLExportResponse,
    status_code=status.HTTP_200_OK,
    summary="Faturayı UBL-TR 1.2 XML formatında dışa aktar",
    description=(
        "E-Fatura entegratörleri ve GİB portalları için standart UBL-TR 1.2 formatında XML ve "
        "metaveri veri paketi üretir."
    )
)
async def export_invoice_ubl(
    invoice_id: int,
    db: Session = Depends(get_db)
):
    return invoice_service.export_invoice_ubl(db=db, invoice_id=invoice_id)
