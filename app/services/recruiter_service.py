from typing import List
from sqlalchemy.orm import Session
from app.models.recruiter import Recruiter
from app.schemas.recruiter import RecruiterCreate
from app.services.company_service import CompanyService
from app.utils.validators import extract_domain
from app.core.exceptions import CustomAPIException
from fastapi import status


class RecruiterService:
    @staticmethod
    def create_recruiter(db: Session, recruiter_in: RecruiterCreate) -> Recruiter:
        # Validate company existence
        CompanyService.get_company(db, recruiter_in.company_id)

        # Extract email domain
        domain = extract_domain(recruiter_in.email)
        if not domain:
            raise CustomAPIException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code="INVALID_EMAIL_DOMAIN",
                message="Could not extract valid domain from recruiter email."
            )

        db_recruiter = Recruiter(
            company_id=recruiter_in.company_id,
            name=recruiter_in.name,
            email=recruiter_in.email.lower(),
            email_domain=domain
        )
        db.add(db_recruiter)
        db.commit()
        db.refresh(db_recruiter)
        return db_recruiter

    @staticmethod
    def get_recruiter(db: Session, recruiter_id: int) -> Recruiter:
        recruiter = db.query(Recruiter).filter(Recruiter.id == recruiter_id).first()
        if not recruiter:
            raise CustomAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                code="RECRUITER_NOT_FOUND",
                message=f"Recruiter with ID {recruiter_id} was not found."
            )
        return recruiter

    @staticmethod
    def get_recruiters_by_company(db: Session, company_id: int) -> List[Recruiter]:
        # Validate company existence
        CompanyService.get_company(db, company_id)
        return db.query(Recruiter).filter(Recruiter.company_id == company_id).all()
