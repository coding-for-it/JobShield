from typing import List, Optional
from pydantic import BaseModel


class ConfusionMatrix(BaseModel):
    true_positives: int    # flagged and really fake
    false_positives: int   # flagged but really real
    false_negatives: int   # fake but not flagged (missed scams)
    true_negatives: int    # real and not flagged


class AnalyticsSummary(BaseModel):
    datasets: List[str]
    total_postings: int
    fraud_postings: int
    fraud_rate_pct: Optional[float] = None
    threshold: int
    confusion_matrix: ConfusionMatrix
    precision_pct: Optional[float] = None
    recall_pct: Optional[float] = None
    accuracy_pct: Optional[float] = None
    always_real_accuracy_pct: Optional[float] = None  # accuracy of a "everything is real" guess


class FraudByRow(BaseModel):
    category: str
    postings: int
    fraud_postings: int
    fraud_pct: float
    fraud_rank: int


class FeatureRow(BaseModel):
    feature: str
    feature_value: int
    postings: int
    fraud_postings: int
    fraud_pct: Optional[float] = None


class RulePerformanceRow(BaseModel):
    signal_type: str
    postings_flagged: int
    fraud_flagged: int
    precision_pct: Optional[float] = None
    coverage_pct: Optional[float] = None
    lift: Optional[float] = None


class ThresholdRow(BaseModel):
    threshold: int
    flagged: int
    true_positives: int
    precision_pct: Optional[float] = None
    recall_pct: Optional[float] = None
