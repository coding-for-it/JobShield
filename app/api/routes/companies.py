from fastapi import APIRouter, Depends, Query, status
from pymysql.connections import Connection
from typing import Optional
from app.database import get_db
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse
from app.utils.pagination import PaginatedResponse
from app.services.company_service import CompanyService
from app.api.deps import get_current_user

router = APIRouter(prefix="/companies", tags=["Companies"])


@router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
def create_company(
    company_in: CompanyCreate,
    db: Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new company record."""
    return CompanyService.create_company(db, company_in)


@router.get("", response_model=PaginatedResponse[CompanyResponse])
def list_companies(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    domain: Optional[str] = Query(None, description="Filter by domain keyword"),
    db: Connection = Depends(get_db)
):
    """List companies with optional domain filter and pagination."""
    companies, total = CompanyService.list_companies(db, page=page, limit=limit, domain=domain)
    return PaginatedResponse.create(data=companies, page=page, limit=limit, total=total)


@router.get("/search", response_model=PaginatedResponse[CompanyResponse])
def search_companies(
    q: str = Query(..., min_length=1, description="Search term for company name, domain, or description"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Connection = Depends(get_db)
):
    """Search companies by keyword."""
    companies, total = CompanyService.search_companies(db, q=q, page=page, limit=limit)
    return PaginatedResponse.create(data=companies, page=page, limit=limit, total=total)


@router.get("/{company_id}", response_model=CompanyResponse)
def get_company(company_id: int, db: Connection = Depends(get_db)):
    """Retrieve details for a specific company by ID."""
    return CompanyService.get_company(db, company_id)


@router.patch("/{company_id}", response_model=CompanyResponse)
def update_company(
    company_id: int,
    company_in: CompanyUpdate,
    db: Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update details of a company."""
    return CompanyService.update_company(db, company_id, company_in)


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(
    company_id: int,
    db: Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a company by ID."""
    CompanyService.delete_company(db, company_id)
    return None
