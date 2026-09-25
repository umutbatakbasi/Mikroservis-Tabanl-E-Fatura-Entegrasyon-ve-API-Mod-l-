from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse
from app.services.customer_service import CustomerService

router = APIRouter(prefix="/customers", tags=["Customers"])
customer_service = CustomerService()


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yeni müşteri oluştur",
    description="Sisteme yeni bir müşteri kaydeder. tax_number (VKN/TCKN) benzersiz olmalıdır."
)
def create_customer(
    customer_in: CustomerCreate,
    db: Session = Depends(get_db)
):
    return customer_service.create_customer(db=db, customer_in=customer_in)


@router.get(
    "",
    response_model=List[CustomerResponse],
    status_code=status.HTTP_200_OK,
    summary="Tüm müşterileri listele",
    description="Kayıtlı tüm müşterileri sayfalanmış şekilde listeler."
)
def get_customers(
    skip: int = Query(0, ge=0, description="Atlanacak kayıt sayısı"),
    limit: int = Query(100, ge=1, le=500, description="Döndürülecek maksimum kayıt sayısı"),
    db: Session = Depends(get_db)
):
    return customer_service.get_all_customers(db=db, skip=skip, limit=limit)


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
    status_code=status.HTTP_200_OK,
    summary="Müşteri detayını getir",
    description="ID'si verilen müşterinin detay bilgilerini getirir."
)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db)
):
    return customer_service.get_customer_by_id(db=db, customer_id=customer_id)


@router.put(
    "/{customer_id}",
    response_model=CustomerResponse,
    status_code=status.HTTP_200_OK,
    summary="Müşteri bilgilerini güncelle",
    description="Mevcut bir müşterinin bilgilerini günceller."
)
def update_customer(
    customer_id: int,
    customer_in: CustomerUpdate,
    db: Session = Depends(get_db)
):
    return customer_service.update_customer(db=db, customer_id=customer_id, customer_in=customer_in)


@router.delete(
    "/{customer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Müşteriyi sil",
    description="ID'si verilen müşteriyi sistemden siler."
)
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db)
):
    customer_service.delete_customer(db=db, customer_id=customer_id)
    return None
