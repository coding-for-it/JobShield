from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel, Field
from app.database import execute_query, fetch_one, fetch_all
from app.routes.auth import get_current_user

router = APIRouter(prefix="/jobs", tags=["Jobs"])


class JobCreate(BaseModel):
    company_id: int
    title: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    location: Optional[str] = None
    job_url: Optional[str] = None
    salary_text: Optional[str] = None
    source: Optional[str] = "Direct"


class JobUpdate(BaseModel):
    company_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    job_url: Optional[str] = None
    salary_text: Optional[str] = None
    source: Optional[str] = None


@router.post("", status_code=status.HTTP_201_CREATED)
def create_job(job_in: JobCreate, current_user: dict = Depends(get_current_user)):
    """Create a new job posting."""
    company = fetch_one("SELECT id FROM companies WHERE id = %s", (job_in.company_id,))
    if not company:
        raise HTTPException(status_code=404, detail={"code": "COMPANY_NOT_FOUND", "message": f"Company {job_in.company_id} not found."})

    job_id = execute_query(
        """
        INSERT INTO jobs (company_id, title, description, location, job_url, salary_text, source)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (job_in.company_id, job_in.title, job_in.description, job_in.location, job_in.job_url, job_in.salary_text, job_in.source)
    )
    job = fetch_one("SELECT * FROM jobs WHERE id = %s", (job_id,))
    if job:
        job["company"] = fetch_one("SELECT * FROM companies WHERE id = %s", (job["company_id"],))
    return job


@router.get("")
def list_jobs(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    company_id: Optional[int] = Query(None),
    location: Optional[str] = Query(None)
):
    """List job postings with optional company and location filters."""
    offset = (page - 1) * limit
    where_clauses = []
    params = []

    if company_id:
        where_clauses.append("company_id = %s")
        params.append(company_id)
    if location:
        where_clauses.append("location LIKE %s")
        params.append(f"%{location}%")

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    total = fetch_one(f"SELECT COUNT(*) as count FROM jobs {where_sql}", tuple(params))["count"]

    query_params = list(params) + [limit, offset]
    jobs = fetch_all(f"SELECT * FROM jobs {where_sql} ORDER BY id DESC LIMIT %s OFFSET %s", tuple(query_params))

    for j in jobs:
        j["company"] = fetch_one("SELECT * FROM companies WHERE id = %s", (j["company_id"],))

    total_pages = (total + limit - 1) // limit if limit > 0 else 0
    return {
        "data": jobs,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages
        }
    }


@router.get("/search")
def search_jobs(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    """Search job postings by title, description, or location."""
    offset = (page - 1) * limit
    pattern = f"%{q}%"
    total = fetch_one("SELECT COUNT(*) as count FROM jobs WHERE title LIKE %s OR description LIKE %s OR location LIKE %s", (pattern, pattern, pattern))["count"]
    jobs = fetch_all("SELECT * FROM jobs WHERE title LIKE %s OR description LIKE %s OR location LIKE %s ORDER BY id DESC LIMIT %s OFFSET %s", (pattern, pattern, pattern, limit, offset))

    for j in jobs:
        j["company"] = fetch_one("SELECT * FROM companies WHERE id = %s", (j["company_id"],))

    total_pages = (total + limit - 1) // limit if limit > 0 else 0
    return {
        "data": jobs,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages
        }
    }


@router.get("/{job_id}")
def get_job(job_id: int):
    """Get single job posting by ID."""
    job = fetch_one("SELECT * FROM jobs WHERE id = %s", (job_id,))
    if not job:
        raise HTTPException(status_code=404, detail={"code": "JOB_NOT_FOUND", "message": f"Job {job_id} not found."})
    job["company"] = fetch_one("SELECT * FROM companies WHERE id = %s", (job["company_id"],))
    return job


@router.patch("/{job_id}")
def update_job(job_id: int, job_in: JobUpdate, current_user: dict = Depends(get_current_user)):
    """Update job posting fields."""
    job = fetch_one("SELECT * FROM jobs WHERE id = %s", (job_id,))
    if not job:
        raise HTTPException(status_code=404, detail={"code": "JOB_NOT_FOUND", "message": f"Job {job_id} not found."})

    company_id = job_in.company_id if job_in.company_id is not None else job["company_id"]
    title = job_in.title if job_in.title is not None else job["title"]
    description = job_in.description if job_in.description is not None else job["description"]
    location = job_in.location if job_in.location is not None else job["location"]
    job_url = job_in.job_url if job_in.job_url is not None else job["job_url"]
    salary_text = job_in.salary_text if job_in.salary_text is not None else job["salary_text"]
    source = job_in.source if job_in.source is not None else job["source"]

    execute_query(
        """
        UPDATE jobs
        SET company_id = %s, title = %s, description = %s, location = %s, job_url = %s, salary_text = %s, source = %s
        WHERE id = %s
        """,
        (company_id, title, description, location, job_url, salary_text, source, job_id)
    )
    job_updated = fetch_one("SELECT * FROM jobs WHERE id = %s", (job_id,))
    job_updated["company"] = fetch_one("SELECT * FROM companies WHERE id = %s", (job_updated["company_id"],))
    return job_updated


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(job_id: int, current_user: dict = Depends(get_current_user)):
    """Delete job posting by ID."""
    job = fetch_one("SELECT * FROM jobs WHERE id = %s", (job_id,))
    if not job:
        raise HTTPException(status_code=404, detail={"code": "JOB_NOT_FOUND", "message": f"Job {job_id} not found."})
    execute_query("DELETE FROM jobs WHERE id = %s", (job_id,))
    return None
