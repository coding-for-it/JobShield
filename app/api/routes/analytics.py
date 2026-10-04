from enum import Enum
from typing import List

from fastapi import APIRouter, Depends, Query
from pymysql.connections import Connection

from app.api.deps import get_current_user
from app.database import get_db
from app.schemas.analytics import (
    AnalyticsSummary, FraudByRow, FeatureRow, RulePerformanceRow, ThresholdRow,
)
from app.services.analytics_service import AnalyticsService

# All analytics endpoints need a login token (same rule as the verification endpoints).
router = APIRouter(prefix="/analytics", tags=["Analytics"], dependencies=[Depends(get_current_user)])


class Dimension(str, Enum):
    """Only these names are accepted in the URL. Anything else returns a 422 error."""
    employment_type = "employment_type"
    industry = "industry"
    required_experience = "required_experience"
    required_education = "required_education"
    job_function = "job_function"
    country = "country"


@router.get("/summary", response_model=AnalyticsSummary)
def get_summary(threshold: int = Query(25, ge=0, le=100, description="Flag postings with risk score >= this"),
                db: Connection = Depends(get_db)):
    """Dataset size, fraud rate, and how well the rule engine does (confusion matrix, precision, recall)."""
    return AnalyticsService.summary(db, threshold)


@router.get("/fraud-by/{dimension}", response_model=List[FraudByRow])
def get_fraud_by(dimension: Dimension,
                 min_postings: int = Query(30, ge=1, description="Ignore groups smaller than this"),
                 limit: int = Query(15, ge=1, le=100),
                 db: Connection = Depends(get_db)):
    """Fraud rate for each category of one column, ranked highest first."""
    return AnalyticsService.fraud_by(db, dimension.value, min_postings, limit)


@router.get("/features", response_model=List[FeatureRow])
def get_features(db: Connection = Depends(get_db)):
    """Fraud rate when a yes/no feature (logo, questions, ...) is absent (0) vs present (1)."""
    return AnalyticsService.features(db)


@router.get("/rule-performance", response_model=List[RulePerformanceRow])
def get_rule_performance(db: Connection = Depends(get_db)):
    """Precision, coverage and lift of each individual rule."""
    return AnalyticsService.rule_performance(db)


@router.get("/threshold-sweep", response_model=List[ThresholdRow])
def get_threshold_sweep(db: Connection = Depends(get_db)):
    """Precision and recall at several flag thresholds."""
    return AnalyticsService.threshold_sweep(db)
