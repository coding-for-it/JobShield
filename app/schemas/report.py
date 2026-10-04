from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class ReportCreate(BaseModel):
    company_id: Optional[int] = Field(None, description="Optional associated company ID")
    job_id: Optional[int] = Field(None, description="Optional associated job ID")
    report_type: str = Field(..., examples=["PAYMENT_REQUEST", "FAKE_INTERVIEW", "SUSPICIOUS_RECRUITER", "FAKE_OFFER", "MISLEADING_JOB", "OTHER"])
    description: str = Field(..., min_length=10, examples=["Recruiter asked for $50 registration fee via gift card before interview."])


class ReportResponse(BaseModel):
    id: int
    user_id: int
    company_id: Optional[int] = None
    job_id: Optional[int] = None
    report_type: str
    description: str
    status: str
    created_at: datetime
