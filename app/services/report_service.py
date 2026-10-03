from typing import List
from sqlalchemy.orm import Session
from app.models.report import Report
from app.schemas.report import ReportCreate
from app.core.exceptions import CustomAPIException
from fastapi import status


class ReportService:
    @staticmethod
    def create_report(db: Session, user_id: int, report_in: ReportCreate) -> Report:
        db_report = Report(
            user_id=user_id,
            company_id=report_in.company_id,
            job_id=report_in.job_id,
            report_type=report_in.report_type,
            description=report_in.description,
            status="PENDING"
        )
        db.add(db_report)
        db.commit()
        db.refresh(db_report)
        return db_report

    @staticmethod
    def get_user_reports(db: Session, user_id: int) -> List[Report]:
        return db.query(Report).filter(Report.user_id == user_id).order_by(Report.id.desc()).all()

    @staticmethod
    def get_report(db: Session, user_id: int, report_id: int) -> Report:
        report = db.query(Report).filter(Report.id == report_id, Report.user_id == user_id).first()
        if not report:
            raise CustomAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                code="REPORT_NOT_FOUND",
                message=f"Report with ID {report_id} was not found."
            )
        return report
