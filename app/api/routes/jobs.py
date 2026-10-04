from fastapi import APIRouter, Depends, Query, status
from pymysql.connections import Connection
from typing import Optional
from app.database import get_db
from app.schemas.job import JobCreate, JobUpdate, JobResponse
from app.utils.pagination import PaginatedResponse
from app.services.job_service import JobService
from app.api.deps import get_current_user

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    job_in: JobCreate,
    db: Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new job posting record."""
    return JobService.create_job(db, job_in)


@router.get("", response_model=PaginatedResponse[JobResponse])
def list_jobs(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    company_id: Optional[int] = Query(None, description="Filter jobs by company ID"),
    location: Optional[str] = Query(None, description="Filter jobs by location keyword"),
    db: Connection = Depends(get_db)
):
    """List job postings with optional company and location filters."""
    jobs, total = JobService.list_jobs(db, page=page, limit=limit, company_id=company_id, location=location)
    return PaginatedResponse.create(data=jobs, page=page, limit=limit, total=total)


@router.get("/search", response_model=PaginatedResponse[JobResponse])
def search_jobs(
    q: str = Query(..., min_length=1, description="Search term for job title, description, or location"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Connection = Depends(get_db)
):
    """Search job postings by keyword."""
    jobs, total = JobService.search_jobs(db, q=q, page=page, limit=limit)
    return PaginatedResponse.create(data=jobs, page=page, limit=limit, total=total)


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Connection = Depends(get_db)):
    """Get detailed information for a single job posting by ID."""
    return JobService.get_job(db, job_id)


@router.patch("/{job_id}", response_model=JobResponse)
def update_job(
    job_id: int,
    job_in: JobUpdate,
    db: Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update job posting details."""
    return JobService.update_job(db, job_id, job_in)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: int,
    db: Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a job posting by ID."""
    JobService.delete_job(db, job_id)
    return None
