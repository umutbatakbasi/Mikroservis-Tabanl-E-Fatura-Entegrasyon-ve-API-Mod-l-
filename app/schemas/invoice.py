from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.customer import CustomerResponse
from app.schemas.product import ProductResponse


class InvoiceLineCreate(BaseModel):
    """Schema for creating a line item within an invoice."""
    product_id: int = Field(..., gt=0, description="Ürün ID'si")
    quantity: Decimal = Field(
        ...,
        gt=0,
        description="Satılan miktar (0'dan büyük olmalıdır)",
        examples=[Decimal("2.00")]
    )


class InvoiceCreate(BaseModel):
    """Schema for creating a new invoice header with its lines."""
    customer_id: int = Field(..., gt=0, description="Müşteri ID'si")
    invoice_date: date = Field(
        ...,
        description="Fatura tarihi (YYYY-MM-DD)",
        examples=["2026-09-25"]
    )
    lines: List[InvoiceLineCreate] = Field(
        ...,
        min_length=1,
        description="Fatura kalemleri (en az bir kalem zorunludur)"
    )


class InvoiceLineResponse(BaseModel):
    """Schema for returning line item details."""
    id: int
    invoice_id: int
    product_id: int
    quantity: Decimal
    unit_price: Decimal
    vat_rate: Decimal
    line_total: Decimal
    vat_amount: Decimal
    product: Optional[ProductResponse] = None

    model_config = ConfigDict(from_attributes=True)


class InvoiceResponse(BaseModel):
    """Schema for returning complete invoice header and its items."""
    id: int
    invoice_number: str
    customer_id: int
    invoice_date: date
    total_amount: Decimal
    total_vat: Decimal
    grand_total: Decimal
    status: str
    uuid: Optional[str] = None
    created_at: datetime
    customer: Optional[CustomerResponse] = None
    lines: List[InvoiceLineResponse] = []

    model_config = ConfigDict(from_attributes=True)


class InvoiceSendResponse(BaseModel):
    """Schema for e-invoice sending status response."""
    success: bool
    message: str
    invoice_id: int
    invoice_number: str
    uuid: str
    status: str
