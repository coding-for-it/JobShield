from typing import List, Optional, Tuple
from fastapi import status
from pymysql.connections import Connection
from app.database import fetch_one, fetch_all, execute, update_row
from app.schemas.job import JobCreate, JobUpdate
from app.services.company_service import CompanyService
from app.core.exceptions import CustomAPIException


class JobService:
    @staticmethod
    def create_job(db: Connection, job_in: JobCreate) -> dict:
        CompanyService.get_company(db, job_in.company_id)  # company must exist

        job_id = execute(
            db,
            """INSERT INTO jobs (company_id, title, description, location, job_url, salary_text, source)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (
                job_in.company_id,
                job_in.title,
                job_in.description,
                job_in.location,
                job_in.job_url,
                job_in.salary_text,
                job_in.source,
            ),
        )
        db.commit()
        return JobService.get_job(db, job_id)

    @staticmethod
    def get_job(db: Connection, job_id: int) -> dict:
        job = fetch_one(db, "SELECT * FROM jobs WHERE id = %s", (job_id,))
        if not job:
            raise CustomAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                code="JOB_NOT_FOUND",
                message=f"Job posting with ID {job_id} was not found.",
            )
        return job

    @staticmethod
    def list_jobs(
        db: Connection,
        page: int = 1,
        limit: int = 10,
        company_id: Optional[int] = None,
        location: Optional[str] = None,
    ) -> Tuple[List[dict], int]:
        conditions, params = [], []
        if company_id:
            conditions.append("company_id = %s")
            params.append(company_id)
        if location:
            conditions.append("location LIKE %s")
            params.append(f"%{location}%")
        where = "WHERE " + " AND ".join(conditions) if conditions else ""

        total = fetch_one(db, f"SELECT COUNT(*) AS total FROM jobs {where}", params)["total"]
        jobs = fetch_all(
            db,
            f"SELECT * FROM jobs {where} ORDER BY id DESC LIMIT %s OFFSET %s",
            [*params, limit, (page - 1) * limit],
        )
        return jobs, total

    @staticmethod
    def search_jobs(db: Connection, q: str, page: int = 1, limit: int = 10) -> Tuple[List[dict], int]:
        where = "WHERE title LIKE %s OR description LIKE %s OR location LIKE %s"
        like = f"%{q}%"
        params = [like, like, like]

        total = fetch_one(db, f"SELECT COUNT(*) AS total FROM jobs {where}", params)["total"]
        jobs = fetch_all(
            db,
            f"SELECT * FROM jobs {where} ORDER BY id DESC LIMIT %s OFFSET %s",
            [*params, limit, (page - 1) * limit],
        )
        return jobs, total

    @staticmethod
    def update_job(db: Connection, job_id: int, job_in: JobUpdate) -> dict:
        JobService.get_job(db, job_id)  # 404 if it does not exist

        fields = job_in.model_dump(exclude_unset=True)
        if fields.get("company_id"):
            CompanyService.get_company(db, fields["company_id"])

        update_row(db, "jobs", job_id, fields)
        return JobService.get_job(db, job_id)

    @staticmethod
    def delete_job(db: Connection, job_id: int) -> None:
        JobService.get_job(db, job_id)  # 404 if it does not exist
        execute(db, "DELETE FROM jobs WHERE id = %s", (job_id,))
        db.commit()
