from fastapi import APIRouter, Depends, status
from pymysql.connections import Connection
from typing import List
from app.database import get_db
from app.schemas.report import ReportCreate, ReportResponse
from app.services.report_service import ReportService
from app.api.deps import get_current_user

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def create_report(
    report_in: ReportCreate,
    db: Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Submit a report for a suspicious job offer, recruiter, or company."""
    return ReportService.create_report(db, current_user["id"], report_in)


@router.get("", response_model=List[ReportResponse])
def list_user_reports(
    db: Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Retrieve all reports submitted by the authenticated user."""
    return ReportService.get_user_reports(db, current_user["id"])


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(
    report_id: int,
    db: Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Retrieve detailed information for a single report by ID."""
    return ReportService.get_report(db, current_user["id"], report_id)
