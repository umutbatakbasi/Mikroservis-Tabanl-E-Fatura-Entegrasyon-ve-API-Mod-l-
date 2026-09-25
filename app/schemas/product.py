from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    """Base product schema with common attributes."""
    code: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Benzersiz ürün veya hizmet kodu",
        examples=["PRD-001"]
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Ürün veya hizmet adı",
        examples=["Bulut Sunucu Hizmeti - 1 Yıllık"]
    )
    description: Optional[str] = Field(
        None,
        description="Ürün açıklaması",
        examples=["Yüksek performanslı bulut barındırma paketi"]
    )
    unit_price: Decimal = Field(
        ...,
        ge=0,
        description="Birim fiyat (KDV hariç)",
        examples=[Decimal("1500.00")]
    )
    vat_rate: Decimal = Field(
        ...,
        ge=0,
        le=100,
        description="KDV oranı (%) (ör. 0, 1, 10, 20)",
        examples=[Decimal("20.00")]
    )


class ProductCreate(ProductBase):
    """Schema for creating a new product."""
    pass


class ProductUpdate(BaseModel):
    """Schema for updating an existing product."""
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    unit_price: Optional[Decimal] = Field(None, ge=0)
    vat_rate: Optional[Decimal] = Field(None, ge=0, le=100)


class ProductResponse(ProductBase):
    """Schema for returning product information."""
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
