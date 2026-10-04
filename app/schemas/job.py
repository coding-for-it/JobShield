from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class JobCreate(BaseModel):
    company_id: int = Field(..., description="Foreign key ID of the hiring company")
    title: str = Field(..., min_length=2, max_length=200, examples=["Backend Python Developer"])
    description: Optional[str] = Field(None, examples=["Build APIs using FastAPI and MySQL."])
    location: Optional[str] = Field(None, examples=["Remote / New York, NY"])
    job_url: Optional[str] = Field(None, examples=["https://example.com/jobs/123"])
    salary_text: Optional[str] = Field(None, examples=["$80,000 - $100,000"])
    source: Optional[str] = Field("Direct", examples=["LinkedIn", "Company Careers Page"])


class JobUpdate(BaseModel):
    company_id: Optional[int] = None
    title: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    location: Optional[str] = None
    job_url: Optional[str] = None
    salary_text: Optional[str] = None
    source: Optional[str] = None


class JobResponse(BaseModel):
    id: int
    company_id: int
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    job_url: Optional[str] = None
    salary_text: Optional[str] = None
    source: Optional[str] = None
    created_at: datetime
    updated_at: datetime
