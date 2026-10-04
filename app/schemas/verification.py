from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List


class EmailVerificationRequest(BaseModel):
    sender_name: str = Field("HR Recruiter", examples=["HR Recruitment Team"])
    sender_email: EmailStr = Field(..., examples=["hr@example.com"])
    subject: str = Field(..., examples=["Congratulations! Job Selection Notice"])
    body: str = Field(..., examples=["You have been selected for the position of Data Analyst..."])
    company_name: str = Field(..., examples=["TechCorp Solutions"])
    company_website: Optional[str] = Field(None, examples=["https://techcorp.com"])


class JobVerificationRequest(BaseModel):
    job_url: str = Field(..., examples=["https://techcorp.com/careers/data-analyst"])
    company_name: Optional[str] = Field(None, examples=["TechCorp Solutions"])


class CompanyVerificationRequest(BaseModel):
    company_name: str = Field(..., examples=["TechCorp Solutions"])
    website: str = Field(..., examples=["https://techcorp.com"])


class SignalResponse(BaseModel):
    id: Optional[int] = None
    signal_type: str
    severity: str
    title: str
    description: Optional[str] = None
    evidence: Optional[str] = None
    score_impact: int


class VerificationResultResponse(BaseModel):
    id: int
    user_id: int
    company_id: Optional[int] = None
    job_id: Optional[int] = None
    verification_type: str
    risk_score: int
    risk_level: str
    verification_status: str
    summary: Optional[str] = None
    created_at: datetime
    signals: List[SignalResponse] = []
    recommended_actions: List[str] = []
