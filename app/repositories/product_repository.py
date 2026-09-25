from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.product import Product
from app.schemas.product import ProductCreate


class ProductRepository:
    """Repository handling database operations for Product entities using SQLAlchemy 2.x."""

    @staticmethod
    def get_by_id(db: Session, product_id: int) -> Optional[Product]:
        stmt = select(Product).where(Product.id == product_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_code(db: Session, code: str) -> Optional[Product]:
        stmt = select(Product).where(Product.code == code)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_ids(db: Session, product_ids: List[int]) -> List[Product]:
        stmt = select(Product).where(Product.id.in_(product_ids))
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[Product]:
        stmt = select(Product).order_by(Product.id.asc()).offset(skip).limit(limit)
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def create(db: Session, product_in: ProductCreate) -> Product:
        product = Product(
            code=product_in.code,
            name=product_in.name,
            description=product_in.description,
            unit_price=product_in.unit_price,
            vat_rate=product_in.vat_rate,
        )
        db.add(product)
        db.flush()
        db.refresh(product)
        return product

    @staticmethod
    def update(db: Session, product: Product, update_data: dict) -> Product:
        for field, value in update_data.items():
            setattr(product, field, value)
        db.flush()
        db.refresh(product)
        return product

    @staticmethod
    def delete(db: Session, product: Product) -> None:
        db.delete(product)
        db.flush()
