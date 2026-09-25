import os
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from app.core.config import settings
from app.routers import customers_router, products_router, invoices_router

# Initialize FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Mikroservis Tabanlı E-Fatura Entegrasyon ve API Modülü.\n\n"
        "ERP faturalama süreçlerini simüle eden, RESTful Müşteri, Ürün ve Fatura yönetimini sağlayan, "
        "GİB / E-Fatura entegratör mimarisine hazır kurumsal backend servisi."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers under configured prefix (/api)
app.include_router(customers_router, prefix=settings.API_V1_PREFIX)
app.include_router(products_router, prefix=settings.API_V1_PREFIX)
app.include_router(invoices_router, prefix=settings.API_V1_PREFIX)

# Also mount under root (/invoices, /customers, /products) for direct endpoint compatibility
app.include_router(invoices_router, prefix="", include_in_schema=False)
app.include_router(customers_router, prefix="", include_in_schema=False)
app.include_router(products_router, prefix="", include_in_schema=False)

# Mount static assets directory
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", tags=["GUI"], response_class=FileResponse)
@app.get("/dashboard", tags=["GUI"], response_class=FileResponse)
async def serve_dashboard():
    """Grafiksel Kullanıcı Arayüzü (GUI) Web Dashboard portalını sunar."""
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return JSONResponse(
        content={
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "healthy",
            "docs_url": "/docs",
            "redoc_url": "/redoc",
            "api_prefix": settings.API_V1_PREFIX,
        }
    )


@app.get("/api", tags=["Root"])
async def api_root():
    """API kök uç noktası: Uygulama metaverilerini ve dokümantasyon bağlantılarını döner."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "healthy",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "api_prefix": settings.API_V1_PREFIX,
    }



@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for container orchestrators and monitoring tools."""
    return {"status": "ok", "app": settings.APP_NAME}


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle Pydantic validation errors (422 Unprocessable Entity)
    with clean, structured Turkish messages.
    """
    errors = []
    for err in exc.errors():
        field = " -> ".join(str(loc) for loc in err["loc"] if loc != "body")
        errors.append({
            "field": field or "body",
            "message": err["msg"],
            "type": err["type"]
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "İstemci tarafından gönderilen veride doğrulama (validation) hatası oluştu.",
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "errors": errors
        }
    )


@app.exception_handler(IntegrityError)
async def integrity_exception_handler(request: Request, exc: IntegrityError):
    """Handle database constraint violations (duplicate keys, foreign key violations)."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "detail": "Veritabanı bütünlük kısıtlaması ihlali (tekil alan çakışması veya geçersiz yabancı anahtar).",
            "status_code": status.HTTP_409_CONFLICT,
            "message": str(exc.orig) if settings.DEBUG else "Database integrity violation"
        }
    )


@app.exception_handler(OperationalError)
async def operational_exception_handler(request: Request, exc: OperationalError):
    """Handle database connection or locking issues."""
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "detail": "Veritabanı kilitlenme veya erişim hatası. Lütfen daha sonra tekrar deneyiniz.",
            "status_code": status.HTTP_503_SERVICE_UNAVAILABLE,
            "message": str(exc.orig) if settings.DEBUG else "Database operational issue"
        }
    )


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """Ensure all HTTPExceptions return uniform JSON format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Fallback exception handler for unhandled exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Sunucu tarafında beklenmeyen bir hata oluştu.",
            "error_type": type(exc).__name__,
            "message": str(exc) if settings.DEBUG else "Internal Server Error"
        },
    )
