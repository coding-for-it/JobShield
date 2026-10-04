from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from app.core.config import settings
from app.core.exceptions import (
    CustomAPIException,
    custom_api_exception_handler,
    validation_exception_handler,
    generic_exception_handler
)
from app.api.router import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API-First Job & Company Verification Platform providing evidence-based risk assessment.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Register Exception Handlers
app.add_exception_handler(CustomAPIException, custom_api_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include V1 API Routes
app.include_router(api_router)


@app.get("/", tags=["Health"])
def root():
    return {
        "success": True,
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }
