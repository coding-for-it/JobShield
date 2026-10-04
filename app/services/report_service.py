from typing import List
from fastapi import status
from pymysql.connections import Connection
from app.database import fetch_one, fetch_all, execute
from app.schemas.report import ReportCreate
from app.core.exceptions import CustomAPIException


class ReportService:
    @staticmethod
    def create_report(db: Connection, user_id: int, report_in: ReportCreate) -> dict:
        report_id = execute(
            db,
            """INSERT INTO reports (user_id, company_id, job_id, report_type, description, status)
               VALUES (%s, %s, %s, %s, %s, 'PENDING')""",
            (user_id, report_in.company_id, report_in.job_id, report_in.report_type, report_in.description),
        )
        db.commit()
        return fetch_one(db, "SELECT * FROM reports WHERE id = %s", (report_id,))

    @staticmethod
    def get_user_reports(db: Connection, user_id: int) -> List[dict]:
        return fetch_all(db, "SELECT * FROM reports WHERE user_id = %s ORDER BY id DESC", (user_id,))

    @staticmethod
    def get_report(db: Connection, user_id: int, report_id: int) -> dict:
        report = fetch_one(
            db, "SELECT * FROM reports WHERE id = %s AND user_id = %s", (report_id, user_id)
        )
        if not report:
            raise CustomAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                code="REPORT_NOT_FOUND",
                message=f"Report with ID {report_id} was not found.",
            )
        return report
