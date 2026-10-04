from fastapi import APIRouter, Depends, status
from pymysql.connections import Connection
from typing import List
from app.database import get_db
from app.schemas.recruiter import RecruiterCreate, RecruiterResponse
from app.services.recruiter_service import RecruiterService
from app.api.deps import get_current_user

router = APIRouter(tags=["Recruiters"])


@router.post("/recruiters", response_model=RecruiterResponse, status_code=status.HTTP_201_CREATED)
def create_recruiter(
    recruiter_in: RecruiterCreate,
    db: Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new recruiter entry."""
    return RecruiterService.create_recruiter(db, recruiter_in)


@router.get("/recruiters/{recruiter_id}", response_model=RecruiterResponse)
def get_recruiter(recruiter_id: int, db: Connection = Depends(get_db)):
    """Retrieve details for a specific recruiter by ID."""
    return RecruiterService.get_recruiter(db, recruiter_id)


@router.get("/companies/{company_id}/recruiters", response_model=List[RecruiterResponse])
def get_company_recruiters(company_id: int, db: Connection = Depends(get_db)):
    """Get all registered recruiters for a specific company."""
    return RecruiterService.get_recruiters_by_company(db, company_id)
