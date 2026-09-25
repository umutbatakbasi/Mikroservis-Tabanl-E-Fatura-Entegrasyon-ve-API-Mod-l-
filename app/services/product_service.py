from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.product import Product
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCreate, ProductUpdate


class ProductService:
    """Service layer handling business logic and validations for Products."""

    def __init__(self, repository: ProductRepository = ProductRepository()):
        self.repository = repository

    def get_all_products(self, db: Session, skip: int = 0, limit: int = 100) -> List[Product]:
        return self.repository.get_all(db=db, skip=skip, limit=limit)

    def get_product_by_id(self, db: Session, product_id: int) -> Product:
        product = self.repository.get_by_id(db=db, product_id=product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found."
            )
        return product

    def create_product(self, db: Session, product_in: ProductCreate) -> Product:
        # Check unique code
        existing = self.repository.get_by_code(db=db, code=product_in.code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product with code '{product_in.code}' already exists."
            )
        try:
            product = self.repository.create(db=db, product_in=product_in)
            db.commit()
            return product
        except Exception:
            db.rollback()
            raise

    def update_product(self, db: Session, product_id: int, product_in: ProductUpdate) -> Product:
        product = self.get_product_by_id(db=db, product_id=product_id)
        update_data = product_in.model_dump(exclude_unset=True)

        if "code" in update_data and update_data["code"] != product.code:
            existing = self.repository.get_by_code(db=db, code=update_data["code"])
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Product with code '{update_data['code']}' already exists."
                )

        try:
            updated = self.repository.update(db=db, product=product, update_data=update_data)
            db.commit()
            return updated
        except Exception:
            db.rollback()
            raise

    def delete_product(self, db: Session, product_id: int) -> None:
        product = self.get_product_by_id(db=db, product_id=product_id)
        try:
            self.repository.delete(db=db, product=product)
            db.commit()
        except Exception:
            db.rollback()
            raise
