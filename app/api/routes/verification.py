from fastapi import APIRouter, Depends, status
from pymysql.connections import Connection
from typing import List
from app.database import get_db
from app.schemas.verification import (
    EmailVerificationRequest,
    JobVerificationRequest,
    CompanyVerificationRequest,
    VerificationResultResponse
)
from app.services.verification_service import VerificationService
from app.api.deps import get_current_user

router = APIRouter(prefix="/verification", tags=["Verification"])


@router.post("/email", response_model=VerificationResultResponse, status_code=status.HTTP_200_OK)
async def verify_email(
    req: EmailVerificationRequest,
    db: Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze recruiter email message, sender domain, and body text for scam/fraud signals.
    """
    return await VerificationService.verify_email(db, current_user["id"], req)


@router.post("/job", response_model=VerificationResultResponse, status_code=status.HTTP_200_OK)
async def verify_job(
    req: JobVerificationRequest,
    db: Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Scrape job posting URL, analyze domain structure, and detect suspicious patterns.
    """
    return await VerificationService.verify_job(db, current_user["id"], req)


@router.post("/company", response_model=VerificationResultResponse, status_code=status.HTTP_200_OK)
async def verify_company(
    req: CompanyVerificationRequest,
    db: Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Verify company website SSL/HTTPS status, domain accessibility, and presence of careers pages.
    """
    return await VerificationService.verify_company(db, current_user["id"], req)


@router.get("/history", response_model=List[VerificationResultResponse])
def get_verification_history(
    db: Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Retrieve history of all verifications performed by current user."""
    return VerificationService.get_user_history(db, current_user["id"])


@router.get("/{verification_id}", response_model=VerificationResultResponse)
def get_verification_details(
    verification_id: int,
    db: Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get detailed verification report by ID including signals and recommended actions."""
    return VerificationService.get_verification_details(db, current_user["id"], verification_id)
