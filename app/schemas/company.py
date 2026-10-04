from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class CompanyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150, examples=["TechCorp Solutions"])
    website: Optional[str] = Field(None, examples=["https://techcorp.com"])
    description: Optional[str] = Field(None, examples=["Software engineering enterprise."])
    careers_url: Optional[str] = Field(None, examples=["https://techcorp.com/careers"])
    verified_domain: bool = Field(False)


class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    website: Optional[str] = None
    domain: Optional[str] = None
    description: Optional[str] = None
    careers_url: Optional[str] = None
    verified_domain: Optional[bool] = None


class CompanyResponse(BaseModel):
    id: int
    name: str
    website: Optional[str] = None
    domain: Optional[str] = None
    description: Optional[str] = None
    careers_url: Optional[str] = None
    verified_domain: bool
    created_at: datetime
    updated_at: datetime
