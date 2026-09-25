from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate


class CustomerRepository:
    """Repository handling database operations for Customer entities using SQLAlchemy 2.x."""

    @staticmethod
    def get_by_id(db: Session, customer_id: int) -> Optional[Customer]:
        stmt = select(Customer).where(Customer.id == customer_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_tax_number(db: Session, tax_number: str) -> Optional[Customer]:
        stmt = select(Customer).where(Customer.tax_number == tax_number)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[Customer]:
        stmt = select(Customer).order_by(Customer.id.asc()).offset(skip).limit(limit)
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def create(db: Session, customer_in: CustomerCreate) -> Customer:
        customer = Customer(
            tax_number=customer_in.tax_number,
            name=customer_in.name,
            email=customer_in.email,
            phone=customer_in.phone,
            address=customer_in.address,
        )
        db.add(customer)
        db.flush()
        db.refresh(customer)
        return customer

    @staticmethod
    def update(db: Session, customer: Customer, update_data: dict) -> Customer:
        for field, value in update_data.items():
            setattr(customer, field, value)
        db.flush()
        db.refresh(customer)
        return customer

    @staticmethod
    def delete(db: Session, customer: Customer) -> None:
        db.delete(customer)
        db.flush()
