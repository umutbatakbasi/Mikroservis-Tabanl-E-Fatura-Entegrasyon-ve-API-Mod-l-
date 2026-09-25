from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.customer import Customer
from app.repositories.customer_repository import CustomerRepository
from app.schemas.customer import CustomerCreate, CustomerUpdate


class CustomerService:
    """Service layer handling business logic and validations for Customers."""

    def __init__(self, repository: CustomerRepository = CustomerRepository()):
        self.repository = repository

    def get_all_customers(self, db: Session, skip: int = 0, limit: int = 100) -> List[Customer]:
        return self.repository.get_all(db=db, skip=skip, limit=limit)

    def get_customer_by_id(self, db: Session, customer_id: int) -> Customer:
        customer = self.repository.get_by_id(db=db, customer_id=customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with ID {customer_id} not found."
            )
        return customer

    def create_customer(self, db: Session, customer_in: CustomerCreate) -> Customer:
        # Check unique tax_number
        existing = self.repository.get_by_tax_number(db=db, tax_number=customer_in.tax_number)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Customer with tax_number '{customer_in.tax_number}' already exists."
            )
        try:
            customer = self.repository.create(db=db, customer_in=customer_in)
            db.commit()
            return customer
        except Exception:
            db.rollback()
            raise

    def update_customer(self, db: Session, customer_id: int, customer_in: CustomerUpdate) -> Customer:
        customer = self.get_customer_by_id(db=db, customer_id=customer_id)
        update_data = customer_in.model_dump(exclude_unset=True)

        if "tax_number" in update_data and update_data["tax_number"] != customer.tax_number:
            existing = self.repository.get_by_tax_number(db=db, tax_number=update_data["tax_number"])
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Customer with tax_number '{update_data['tax_number']}' already exists."
                )

        try:
            updated = self.repository.update(db=db, customer=customer, update_data=update_data)
            db.commit()
            return updated
        except Exception:
            db.rollback()
            raise

    def delete_customer(self, db: Session, customer_id: int) -> None:
        customer = self.get_customer_by_id(db=db, customer_id=customer_id)
        try:
            self.repository.delete(db=db, customer=customer)
            db.commit()
        except Exception:
            db.rollback()
            raise
