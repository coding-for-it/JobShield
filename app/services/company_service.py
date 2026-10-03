from typing import Tuple, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.company import Company
from app.schemas.company import CompanyCreate, CompanyUpdate
from app.utils.validators import extract_domain
from app.core.exceptions import CustomAPIException
from fastapi import status


class CompanyService:
    @staticmethod
    def create_company(db: Session, company_in: CompanyCreate) -> Company:
        domain = extract_domain(company_in.website) if company_in.website else None
        
        db_company = Company(
            name=company_in.name,
            website=company_in.website,
            domain=domain,
            description=company_in.description,
            careers_url=company_in.careers_url,
            verified_domain=company_in.verified_domain
        )
        db.add(db_company)
        db.commit()
        db.refresh(db_company)
        return db_company

    @staticmethod
    def get_company(db: Session, company_id: int) -> Company:
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise CustomAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                code="COMPANY_NOT_FOUND",
                message=f"Company with ID {company_id} was not found."
            )
        return company

    @staticmethod
    def list_companies(
        db: Session,
        page: int = 1,
        limit: int = 10,
        domain: Optional[str] = None
    ) -> Tuple[List[Company], int]:
        query = db.query(Company)
        if domain:
            query = query.filter(Company.domain.ilike(f"%{domain}%"))

        total = query.count()
        offset = (page - 1) * limit
        companies = query.order_by(Company.id.desc()).offset(offset).limit(limit).all()
        return companies, total

    @staticmethod
    def search_companies(
        db: Session,
        q: str,
        page: int = 1,
        limit: int = 10
    ) -> Tuple[List[Company], int]:
        query = db.query(Company).filter(
            or_(
                Company.name.ilike(f"%{q}%"),
                Company.domain.ilike(f"%{q}%"),
                Company.description.ilike(f"%{q}%")
            )
        )
        total = query.count()
        offset = (page - 1) * limit
        companies = query.order_by(Company.id.desc()).offset(offset).limit(limit).all()
        return companies, total

    @staticmethod
    def update_company(db: Session, company_id: int, company_in: CompanyUpdate) -> Company:
        company = CompanyService.get_company(db, company_id)

        update_data = company_in.model_dump(exclude_unset=True)
        if "website" in update_data and update_data["website"]:
            update_data["domain"] = extract_domain(update_data["website"])

        for field, value in update_data.items():
            setattr(company, field, value)

        db.commit()
        db.refresh(company)
        return company

    @staticmethod
    def delete_company(db: Session, company_id: int) -> None:
        company = CompanyService.get_company(db, company_id)
        db.delete(company)
        db.commit()
