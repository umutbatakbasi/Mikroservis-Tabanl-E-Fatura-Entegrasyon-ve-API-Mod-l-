from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])
product_service = ProductService()


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yeni ürün oluştur",
    description="Sisteme yeni bir ürün veya hizmet kaydeder. code benzersiz olmalıdır."
)
def create_product(
    product_in: ProductCreate,
    db: Session = Depends(get_db)
):
    return product_service.create_product(db=db, product_in=product_in)


@router.get(
    "",
    response_model=List[ProductResponse],
    status_code=status.HTTP_200_OK,
    summary="Ürünleri listele",
    description="Kayıtlı tüm ürünleri sayfalanmış şekilde listeler."
)
def get_products(
    skip: int = Query(0, ge=0, description="Atlanacak kayıt sayısı"),
    limit: int = Query(100, ge=1, le=500, description="Döndürülecek maksimum kayıt sayısı"),
    db: Session = Depends(get_db)
):
    return product_service.get_all_products(db=db, skip=skip, limit=limit)


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Ürün detayını getir",
    description="ID'si verilen ürünün detay bilgilerini getirir."
)
def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    return product_service.get_product_by_id(db=db, product_id=product_id)


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Ürünü güncelle",
    description="Mevcut bir ürünün bilgilerini günceller."
)
def update_product(
    product_id: int,
    product_in: ProductUpdate,
    db: Session = Depends(get_db)
):
    return product_service.update_product(db=db, product_id=product_id, product_in=product_in)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Ürünü sil",
    description="ID'si verilen ürünü sistemden siler."
)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    product_service.delete_product(db=db, product_id=product_id)
    return None
