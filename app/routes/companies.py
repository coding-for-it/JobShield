from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel, Field
from app.database import execute_query, fetch_one, fetch_all
from app.routes.auth import get_current_user
from app.verification.url_checker import extract_domain

router = APIRouter(prefix="/companies", tags=["Companies"])


class CompanyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    website: Optional[str] = None
    description: Optional[str] = None
    careers_url: Optional[str] = None
    verified_domain: bool = False


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    careers_url: Optional[str] = None
    verified_domain: Optional[bool] = None


@router.post("", status_code=status.HTTP_201_CREATED)
def create_company(company_in: CompanyCreate, current_user: dict = Depends(get_current_user)):
    """Create a company record."""
    domain = extract_domain(company_in.website) if company_in.website else None
    comp_id = execute_query(
        """
        INSERT INTO companies (name, website, domain, description, careers_url, verified_domain)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (company_in.name, company_in.website, domain, company_in.description, company_in.careers_url, company_in.verified_domain)
    )
    return fetch_one("SELECT * FROM companies WHERE id = %s", (comp_id,))


@router.get("")
def list_companies(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    domain: Optional[str] = Query(None)
):
    """List companies with pagination and optional domain filter."""
    offset = (page - 1) * limit
    if domain:
        total = fetch_one("SELECT COUNT(*) as count FROM companies WHERE domain LIKE %s", (f"%{domain}%",))["count"]
        companies = fetch_all("SELECT * FROM companies WHERE domain LIKE %s ORDER BY id DESC LIMIT %s OFFSET %s", (f"%{domain}%", limit, offset))
    else:
        total = fetch_one("SELECT COUNT(*) as count FROM companies")["count"]
        companies = fetch_all("SELECT * FROM companies ORDER BY id DESC LIMIT %s OFFSET %s", (limit, offset))

    total_pages = (total + limit - 1) // limit if limit > 0 else 0
    return {
        "data": companies,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages
        }
    }


@router.get("/search")
def search_companies(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    """Search companies by name or domain."""
    offset = (page - 1) * limit
    search_pattern = f"%{q}%"
    total = fetch_one("SELECT COUNT(*) as count FROM companies WHERE name LIKE %s OR domain LIKE %s", (search_pattern, search_pattern))["count"]
    companies = fetch_all("SELECT * FROM companies WHERE name LIKE %s OR domain LIKE %s ORDER BY id DESC LIMIT %s OFFSET %s", (search_pattern, search_pattern, limit, offset))

    total_pages = (total + limit - 1) // limit if limit > 0 else 0
    return {
        "data": companies,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages
        }
    }


@router.get("/{company_id}")
def get_company(company_id: int):
    """Get company details by ID."""
    company = fetch_one("SELECT * FROM companies WHERE id = %s", (company_id,))
    if not company:
        raise HTTPException(status_code=404, detail={"code": "COMPANY_NOT_FOUND", "message": f"Company {company_id} not found."})
    return company


@router.patch("/{company_id}")
def update_company(company_id: int, company_in: CompanyUpdate, current_user: dict = Depends(get_current_user)):
    """Update company details."""
    company = fetch_one("SELECT * FROM companies WHERE id = %s", (company_id,))
    if not company:
        raise HTTPException(status_code=404, detail={"code": "COMPANY_NOT_FOUND", "message": f"Company {company_id} not found."})

    name = company_in.name if company_in.name is not None else company["name"]
    website = company_in.website if company_in.website is not None else company["website"]
    description = company_in.description if company_in.description is not None else company["description"]
    careers_url = company_in.careers_url if company_in.careers_url is not None else company["careers_url"]
    verified_domain = company_in.verified_domain if company_in.verified_domain is not None else company["verified_domain"]
    domain = extract_domain(website) if website else company["domain"]

    execute_query(
        """
        UPDATE companies
        SET name = %s, website = %s, domain = %s, description = %s, careers_url = %s, verified_domain = %s
        WHERE id = %s
        """,
        (name, website, domain, description, careers_url, verified_domain, company_id)
    )
    return fetch_one("SELECT * FROM companies WHERE id = %s", (company_id,))


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(company_id: int, current_user: dict = Depends(get_current_user)):
    """Delete company by ID."""
    company = fetch_one("SELECT * FROM companies WHERE id = %s", (company_id,))
    if not company:
        raise HTTPException(status_code=404, detail={"code": "COMPANY_NOT_FOUND", "message": f"Company {company_id} not found."})
    execute_query("DELETE FROM companies WHERE id = %s", (company_id,))
    return None
