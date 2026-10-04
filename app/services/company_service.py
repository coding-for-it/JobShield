from typing import List, Optional, Tuple
from fastapi import status
from pymysql.connections import Connection
from app.database import fetch_one, fetch_all, execute, update_row
from app.schemas.company import CompanyCreate, CompanyUpdate
from app.utils.validators import extract_domain
from app.core.exceptions import CustomAPIException


class CompanyService:
    @staticmethod
    def create_company(db: Connection, company_in: CompanyCreate) -> dict:
        domain = extract_domain(company_in.website) if company_in.website else None

        company_id = execute(
            db,
            """INSERT INTO companies (name, website, domain, description, careers_url, verified_domain)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (
                company_in.name,
                company_in.website,
                domain,
                company_in.description,
                company_in.careers_url,
                company_in.verified_domain,
            ),
        )
        db.commit()
        return CompanyService.get_company(db, company_id)

    @staticmethod
    def get_company(db: Connection, company_id: int) -> dict:
        company = fetch_one(db, "SELECT * FROM companies WHERE id = %s", (company_id,))
        if not company:
            raise CustomAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                code="COMPANY_NOT_FOUND",
                message=f"Company with ID {company_id} was not found.",
            )
        return company

    @staticmethod
    def list_companies(
        db: Connection, page: int = 1, limit: int = 10, domain: Optional[str] = None
    ) -> Tuple[List[dict], int]:
        where, params = "", []
        if domain:
            where = "WHERE domain LIKE %s"
            params.append(f"%{domain}%")

        total = fetch_one(db, f"SELECT COUNT(*) AS total FROM companies {where}", params)["total"]
        companies = fetch_all(
            db,
            f"SELECT * FROM companies {where} ORDER BY id DESC LIMIT %s OFFSET %s",
            [*params, limit, (page - 1) * limit],
        )
        return companies, total

    @staticmethod
    def search_companies(db: Connection, q: str, page: int = 1, limit: int = 10) -> Tuple[List[dict], int]:
        where = "WHERE name LIKE %s OR domain LIKE %s OR description LIKE %s"
        like = f"%{q}%"
        params = [like, like, like]

        total = fetch_one(db, f"SELECT COUNT(*) AS total FROM companies {where}", params)["total"]
        companies = fetch_all(
            db,
            f"SELECT * FROM companies {where} ORDER BY id DESC LIMIT %s OFFSET %s",
            [*params, limit, (page - 1) * limit],
        )
        return companies, total

    @staticmethod
    def update_company(db: Connection, company_id: int, company_in: CompanyUpdate) -> dict:
        CompanyService.get_company(db, company_id)  # 404 if it does not exist

        fields = company_in.model_dump(exclude_unset=True)
        if fields.get("website"):
            fields["domain"] = extract_domain(fields["website"])

        update_row(db, "companies", company_id, fields)
        return CompanyService.get_company(db, company_id)

    @staticmethod
    def delete_company(db: Connection, company_id: int) -> None:
        CompanyService.get_company(db, company_id)  # 404 if it does not exist
        # Jobs and recruiters are removed automatically by ON DELETE CASCADE in the schema
        execute(db, "DELETE FROM companies WHERE id = %s", (company_id,))
        db.commit()
