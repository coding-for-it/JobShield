from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class RecruiterCreate(BaseModel):
    company_id: int = Field(..., description="ID of associated company")
    name: str = Field(..., min_length=2, max_length=150, examples=["Alice Smith"])
    email: EmailStr = Field(..., examples=["alice.smith@techcorp.com"])


class RecruiterResponse(BaseModel):
    id: int
    company_id: int
    name: str
    email: EmailStr
    email_domain: str
    created_at: datetime
