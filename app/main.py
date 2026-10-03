from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.database import init_db
from app.routes import auth, companies, jobs, verification, reports
from app.core.exceptions import (
    CustomAPIException,
    custom_api_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
)


app = FastAPI(
    title="JobShield",
    version="1.0.0",
    description="API for job, recruiter, and company verification.",
    docs_url="/docs",
    redoc_url="/redoc",
)


# Register exception handlers
app.add_exception_handler(
    CustomAPIException,
    custom_api_exception_handler
)

app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler
)

app.add_exception_handler(
    Exception,
    generic_exception_handler
)


# Register API routes
app.include_router(auth.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(verification.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")


@app.on_event("startup")
def startup():
    """
    Create the required MySQL tables when the application starts.
    """
    init_db()


@app.get("/", tags=["Health"])
def root():
    return {
        "success": True,
        "message": "Welcome to JobShield",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "JobShield",
        "version": "1.0.0"
    }