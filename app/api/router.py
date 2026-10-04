from fastapi import APIRouter
from app.api.routes import auth, users, companies, jobs, recruiters, verification, reports, analytics

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(companies.router)
api_router.include_router(jobs.router)
api_router.include_router(recruiters.router)
api_router.include_router(verification.router)
api_router.include_router(reports.router)
api_router.include_router(analytics.router)
