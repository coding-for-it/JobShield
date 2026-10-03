from typing import Tuple, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.job import Job
from app.schemas.job import JobCreate, JobUpdate
from app.services.company_service import CompanyService
from app.core.exceptions import CustomAPIException
from fastapi import status


class JobService:
    @staticmethod
    def create_job(db: Session, job_in: JobCreate) -> Job:
        # Ensure company exists
        CompanyService.get_company(db, job_in.company_id)

        db_job = Job(
            company_id=job_in.company_id,
            title=job_in.title,
            description=job_in.description,
            location=job_in.location,
            job_url=job_in.job_url,
            salary_text=job_in.salary_text,
            source=job_in.source
        )
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        return db_job

    @staticmethod
    def get_job(db: Session, job_id: int) -> Job:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise CustomAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                code="JOB_NOT_FOUND",
                message=f"Job posting with ID {job_id} was not found."
            )
        return job

    @staticmethod
    def list_jobs(
        db: Session,
        page: int = 1,
        limit: int = 10,
        company_id: Optional[int] = None,
        location: Optional[str] = None
    ) -> Tuple[List[Job], int]:
        query = db.query(Job)
        if company_id:
            query = query.filter(Job.company_id == company_id)
        if location:
            query = query.filter(Job.location.ilike(f"%{location}%"))

        total = query.count()
        offset = (page - 1) * limit
        jobs = query.order_by(Job.id.desc()).offset(offset).limit(limit).all()
        return jobs, total

    @staticmethod
    def search_jobs(
        db: Session,
        q: str,
        page: int = 1,
        limit: int = 10
    ) -> Tuple[List[Job], int]:
        query = db.query(Job).filter(
            or_(
                Job.title.ilike(f"%{q}%"),
                Job.description.ilike(f"%{q}%"),
                Job.location.ilike(f"%{q}%")
            )
        )
        total = query.count()
        offset = (page - 1) * limit
        jobs = query.order_by(Job.id.desc()).offset(offset).limit(limit).all()
        return jobs, total

    @staticmethod
    def update_job(db: Session, job_id: int, job_in: JobUpdate) -> Job:
        job = JobService.get_job(db, job_id)

        update_data = job_in.model_dump(exclude_unset=True)
        if "company_id" in update_data and update_data["company_id"]:
            CompanyService.get_company(db, update_data["company_id"])

        for field, value in update_data.items():
            setattr(job, field, value)

        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def delete_job(db: Session, job_id: int) -> None:
        job = JobService.get_job(db, job_id)
        db.delete(job)
        db.commit()
