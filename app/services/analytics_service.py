"""
Read-only analytics queries over the job_postings / posting_signals tables.

The same questions are written as stand-alone .sql files in sql/analysis/ (run them with
`python -m etl.run_analysis`). Here they are wrapped so the dashboard can call them.

SQL-injection note: column names can NOT be sent as %s placeholders. So any column name that
appears in the SQL text comes from the fixed whitelists below, never from the request.
Only numbers (threshold, minimum group size, limit) come from the request, as %s values.
"""
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pymysql.connections import Connection

from app.database import fetch_all, fetch_one

# the only columns a client may group by (key = name in the URL, value = real column)
DIMENSION_COLUMNS = {
    "employment_type": "employment_type",
    "industry": "industry",
    "required_experience": "required_experience",
    "required_education": "required_education",
    "job_function": "job_function",
    "country": "country",
}
BINARY_FEATURES = ["has_company_logo", "has_questions", "has_company_profile",
                   "has_salary", "telecommuting", "has_requirements"]
SWEEP_THRESHOLDS = [5, 10, 15, 20, 25, 30, 40, 50, 60, 75]


def _num(value: Any) -> Optional[float]:
    """MySQL returns Decimal for SUM/AVG/ROUND; turn it into a normal number (None stays None)."""
    if value is None:
        return None
    return float(value) if isinstance(value, Decimal) else value


def _int(value: Any) -> int:
    return int(value) if value is not None else 0


def _pct(part: int, whole: int) -> Optional[float]:
    return round(100 * part / whole, 2) if whole else None


class AnalyticsService:
    @staticmethod
    def summary(db: Connection, threshold: int) -> Dict[str, Any]:
        row = fetch_one(
            db,
            """SELECT COUNT(*) AS total,
                      COALESCE(SUM(fraudulent), 0) AS fraud,
                      COALESCE(SUM(risk_score >= %s AND fraudulent = 1), 0) AS tp,
                      COALESCE(SUM(risk_score >= %s AND fraudulent = 0), 0) AS fp,
                      COALESCE(SUM(risk_score <  %s AND fraudulent = 1), 0) AS fn,
                      COALESCE(SUM(risk_score <  %s AND fraudulent = 0), 0) AS tn
               FROM job_postings""",
            (threshold, threshold, threshold, threshold),
        )
        datasets = [r["dataset_name"] for r in
                    fetch_all(db, "SELECT DISTINCT dataset_name FROM job_postings ORDER BY dataset_name")]
        total, fraud = _int(row["total"]), _int(row["fraud"])
        tp, fp, fn, tn = (_int(row[k]) for k in ("tp", "fp", "fn", "tn"))
        return {
            "datasets": datasets,
            "total_postings": total,
            "fraud_postings": fraud,
            "fraud_rate_pct": _pct(fraud, total),
            "threshold": threshold,
            "confusion_matrix": {"true_positives": tp, "false_positives": fp,
                                 "false_negatives": fn, "true_negatives": tn},
            "precision_pct": _pct(tp, tp + fp),
            "recall_pct": _pct(tp, tp + fn),
            "accuracy_pct": _pct(tp + tn, total),
            "always_real_accuracy_pct": _pct(total - fraud, total),
        }

    @staticmethod
    def fraud_by(db: Connection, dimension: str, min_postings: int, limit: int) -> List[Dict[str, Any]]:
        column = DIMENSION_COLUMNS[dimension]  # KeyError is impossible: the route only allows these keys
        rows = fetch_all(
            db,
            f"""SELECT category, postings, fraud_postings, fraud_pct,
                       RANK() OVER (ORDER BY fraud_pct DESC) AS fraud_rank
                FROM (
                    SELECT COALESCE({column}, 'Not specified') AS category,
                           COUNT(*) AS postings,
                           SUM(fraudulent) AS fraud_postings,
                           ROUND(100 * AVG(fraudulent), 2) AS fraud_pct
                    FROM job_postings
                    GROUP BY COALESCE({column}, 'Not specified')
                    HAVING COUNT(*) >= %s
                ) AS grouped
                ORDER BY fraud_rank, postings DESC
                LIMIT %s""",
            (min_postings, limit),
        )
        return [{"category": r["category"], "postings": _int(r["postings"]),
                 "fraud_postings": _int(r["fraud_postings"]), "fraud_pct": _num(r["fraud_pct"]),
                 "fraud_rank": _int(r["fraud_rank"])} for r in rows]

    @staticmethod
    def features(db: Connection) -> List[Dict[str, Any]]:
        sql = " UNION ALL ".join(
            f"SELECT '{name}' AS feature, {name} AS feature_value, COUNT(*) AS postings, "
            f"SUM(fraudulent) AS fraud_postings, ROUND(100 * AVG(fraudulent), 2) AS fraud_pct "
            f"FROM job_postings GROUP BY {name}"
            for name in BINARY_FEATURES  # fixed list above, not user input
        ) + " ORDER BY feature, feature_value"
        return [{"feature": r["feature"], "feature_value": _int(r["feature_value"]),
                 "postings": _int(r["postings"]), "fraud_postings": _int(r["fraud_postings"]),
                 "fraud_pct": _num(r["fraud_pct"])} for r in fetch_all(db, sql)]

    @staticmethod
    def rule_performance(db: Connection) -> List[Dict[str, Any]]:
        rows = fetch_all(
            db,
            """WITH totals AS (SELECT COUNT(*) AS n, SUM(fraudulent) AS fraud_n FROM job_postings)
               SELECT s.signal_type,
                      COUNT(DISTINCT s.posting_id) AS postings_flagged,
                      COUNT(DISTINCT CASE WHEN p.fraudulent = 1 THEN p.id END) AS fraud_flagged,
                      ROUND(100 * COUNT(DISTINCT CASE WHEN p.fraudulent = 1 THEN p.id END)
                            / COUNT(DISTINCT s.posting_id), 2) AS precision_pct,
                      ROUND(100 * COUNT(DISTINCT CASE WHEN p.fraudulent = 1 THEN p.id END)
                            / NULLIF(t.fraud_n, 0), 2) AS coverage_pct,
                      ROUND((COUNT(DISTINCT CASE WHEN p.fraudulent = 1 THEN p.id END)
                             / COUNT(DISTINCT s.posting_id)) / NULLIF(t.fraud_n / t.n, 0), 2) AS lift
               FROM posting_signals s
               JOIN job_postings p ON p.id = s.posting_id
               CROSS JOIN totals t
               GROUP BY s.signal_type, t.n, t.fraud_n
               ORDER BY precision_pct DESC, postings_flagged DESC""",
        )
        return [{"signal_type": r["signal_type"], "postings_flagged": _int(r["postings_flagged"]),
                 "fraud_flagged": _int(r["fraud_flagged"]), "precision_pct": _num(r["precision_pct"]),
                 "coverage_pct": _num(r["coverage_pct"]), "lift": _num(r["lift"])} for r in rows]

    @staticmethod
    def threshold_sweep(db: Connection) -> List[Dict[str, Any]]:
        thresholds = " UNION ALL ".join(
            f"SELECT {int(t)}" + (" AS threshold" if i == 0 else "")
            for i, t in enumerate(SWEEP_THRESHOLDS)  # fixed list above, not user input
        )
        rows = fetch_all(
            db,
            f"""WITH thresholds AS ({thresholds})
                SELECT t.threshold,
                       COALESCE(SUM(p.risk_score >= t.threshold), 0) AS flagged,
                       COALESCE(SUM(p.risk_score >= t.threshold AND p.fraudulent = 1), 0) AS true_positives,
                       ROUND(100 * SUM(p.risk_score >= t.threshold AND p.fraudulent = 1)
                             / NULLIF(SUM(p.risk_score >= t.threshold), 0), 2) AS precision_pct,
                       ROUND(100 * SUM(p.risk_score >= t.threshold AND p.fraudulent = 1)
                             / NULLIF(SUM(p.fraudulent = 1), 0), 2) AS recall_pct
                FROM thresholds t
                CROSS JOIN job_postings p
                GROUP BY t.threshold
                ORDER BY t.threshold""",
        )
        return [{"threshold": _int(r["threshold"]), "flagged": _int(r["flagged"]),
                 "true_positives": _int(r["true_positives"]), "precision_pct": _num(r["precision_pct"]),
                 "recall_pct": _num(r["recall_pct"])} for r in rows]
