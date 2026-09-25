from app.routers.customers import router as customers_router
from app.routers.products import router as products_router
from app.routers.invoices import router as invoices_router

__all__ = [
    "customers_router",
    "products_router",
    "invoices_router",
]
