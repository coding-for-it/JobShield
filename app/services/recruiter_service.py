from typing import List
from fastapi import status
from pymysql.connections import Connection
from app.database import fetch_one, fetch_all, execute
from app.schemas.recruiter import RecruiterCreate
from app.services.company_service import CompanyService
from app.utils.validators import extract_domain
from app.core.exceptions import CustomAPIException


class RecruiterService:
    @staticmethod
    def create_recruiter(db: Connection, recruiter_in: RecruiterCreate) -> dict:
        CompanyService.get_company(db, recruiter_in.company_id)  # company must exist

        domain = extract_domain(recruiter_in.email)
        if not domain:
            raise CustomAPIException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code="INVALID_EMAIL_DOMAIN",
                message="Could not extract valid domain from recruiter email.",
            )

        recruiter_id = execute(
            db,
            "INSERT INTO recruiters (company_id, name, email, email_domain) VALUES (%s, %s, %s, %s)",
            (recruiter_in.company_id, recruiter_in.name, recruiter_in.email.lower(), domain),
        )
        db.commit()
        return RecruiterService.get_recruiter(db, recruiter_id)

    @staticmethod
    def get_recruiter(db: Connection, recruiter_id: int) -> dict:
        recruiter = fetch_one(db, "SELECT * FROM recruiters WHERE id = %s", (recruiter_id,))
        if not recruiter:
            raise CustomAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                code="RECRUITER_NOT_FOUND",
                message=f"Recruiter with ID {recruiter_id} was not found.",
            )
        return recruiter

    @staticmethod
    def get_recruiters_by_company(db: Connection, company_id: int) -> List[dict]:
        CompanyService.get_company(db, company_id)  # 404 if company does not exist
        return fetch_all(db, "SELECT * FROM recruiters WHERE company_id = %s", (company_id,))
