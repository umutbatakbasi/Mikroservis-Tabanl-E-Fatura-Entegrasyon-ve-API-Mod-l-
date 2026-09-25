from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CustomerBase(BaseModel):
    """Base customer schema with common attributes."""
    tax_number: str = Field(
        ...,
        min_length=10,
        max_length=20,
        description="Vergi Kimlik Numarası (VKN) veya TCKN",
        examples=["1234567890"]
    )
    name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Müşteri adı veya unvanı",
        examples=["ABC Teknoloji A.Ş."]
    )
    email: Optional[EmailStr] = Field(
        None,
        description="E-posta adresi",
        examples=["muhasebe@abcteknoloji.com"]
    )
    phone: Optional[str] = Field(
        None,
        max_length=50,
        description="Telefon numarası",
        examples=["+90 212 555 0100"]
    )
    address: Optional[str] = Field(
        None,
        description="Fatura adresi",
        examples=["Büyükdere Cad. No:100 Levent / İstanbul"]
    )


class CustomerCreate(CustomerBase):
    """Schema for creating a new customer."""
    pass


class CustomerUpdate(BaseModel):
    """Schema for updating an existing customer."""
    tax_number: Optional[str] = Field(None, min_length=10, max_length=20)
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None


class CustomerResponse(CustomerBase):
    """Schema for returning customer information."""
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
