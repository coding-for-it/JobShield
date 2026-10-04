"""
Load a labelled job-posting CSV into MySQL.

    python -m etl.load_postings                              (loads the small SAMPLE file)
    python -m etl.load_postings --csv data/fake_job_postings.csv

Steps:  read CSV -> clean (etl/clean.py) -> score each posting with the rule engine
        -> insert postings -> insert the signals that fired.
"""
import argparse
import sys
from pathlib import Path
from typing import Any, Dict

import pandas as pd
from pymysql.connections import Connection

from app.database import get_connection
from app.verification.posting_analyzer import PostingAnalyzer
from app.verification.risk_engine import RiskEngine
from etl.clean import clean_postings

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV = PROJECT_ROOT / "data" / "sample_job_postings_SYNTHETIC.csv"
MAX_DESCRIPTION_CHARS = 60000  # TEXT column limit is ~65,000 bytes

# widths of the short text columns in sql/analytics_schema.sql (a longer value would make MySQL reject the row)
TEXT_LIMITS = {
    "title": 255, "country": 50, "state": 100, "city": 255, "department": 255,
    "employment_type": 50, "required_experience": 50, "required_education": 100,
    "industry": 100, "job_function": 100,
}

POSTING_COLUMNS = [
    "source_job_id", "dataset_name", "title", "country", "state", "city", "department",
    "salary_min", "salary_max", "has_salary", "has_company_profile", "has_requirements",
    "has_benefits", "telecommuting", "has_company_logo", "has_questions",
    "employment_type", "required_experience", "required_education", "industry",
    "job_function", "description", "description_length", "fraudulent",
    "risk_score", "risk_level",
]
INSERT_POSTING_SQL = (
    f"INSERT INTO job_postings ({', '.join(POSTING_COLUMNS)}) "
    f"VALUES ({', '.join(['%s'] * len(POSTING_COLUMNS))})"
)
INSERT_SIGNAL_SQL = (
    "INSERT INTO posting_signals (posting_id, signal_type, severity, score_impact) "
    "VALUES (%s, %s, %s, %s)"
)


def _py(value: Any) -> Any:
    """Convert pandas/numpy values to plain Python values (NaN/NA -> None) for MySQL."""
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value.item() if hasattr(value, "item") else value


def _batches(items: list, size: int):
    for start in range(0, len(items), size):
        yield items[start:start + size]


def load_dataframe(
    conn: Connection,
    raw: pd.DataFrame,
    dataset_name: str,
    replace: bool = True,
    batch_size: int = 1000,
) -> Dict[str, int]:
    """Clean + score + insert. Returns a dict of counts. `replace=True` empties the tables first
    (the tables hold ONE dataset at a time, so results are never mixed)."""
    df, stats = clean_postings(raw)

    # --- score every posting with the rule engine ---
    rows, signal_rows, truncated = [], [], 0
    for record in df.to_dict("records"):
        signals = PostingAnalyzer.analyze(record)
        risk_score, risk_level, _status, _actions = RiskEngine.calculate_risk_score(signals)
        record["dataset_name"] = dataset_name
        record["source_job_id"] = int(record["job_id"])
        record["risk_score"] = risk_score
        record["risk_level"] = risk_level
        for column, limit in TEXT_LIMITS.items():
            value = record.get(column)
            if isinstance(value, str) and len(value) > limit:
                record[column] = value[:limit]
                truncated += 1
        description = record.get("description")
        record["description"] = description[:MAX_DESCRIPTION_CHARS] if isinstance(description, str) else None
        rows.append([_py(record.get(col)) for col in POSTING_COLUMNS])
        signal_rows.append((record["source_job_id"], signals))

    try:
        with conn.cursor() as cur:
            if replace:
                cur.execute("DELETE FROM posting_signals")
                cur.execute("DELETE FROM job_postings")

            for chunk in _batches(rows, batch_size):
                cur.executemany(INSERT_POSTING_SQL, chunk)

            # map the original job id to the new MySQL id, so signals can point to their posting
            cur.execute("SELECT id, source_job_id FROM job_postings WHERE dataset_name = %s", (dataset_name,))
            id_map = {r["source_job_id"]: r["id"] for r in cur.fetchall()}

            signal_values = [
                (id_map[job_id], s["signal_type"], s["severity"], s["score_impact"])
                for job_id, signals in signal_rows for s in signals
            ]
            for chunk in _batches(signal_values, batch_size * 5):
                cur.executemany(INSERT_SIGNAL_SQL, chunk)
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    stats["signals_inserted"] = len(signal_values)
    stats["values_truncated"] = truncated
    stats["flagged_at_25"] = sum(1 for r in rows if r[POSTING_COLUMNS.index("risk_score")] >= 25)
    return stats


def read_csv(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path, encoding="utf-8")
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="latin-1")


def main() -> int:
    parser = argparse.ArgumentParser(description="Load a labelled job-posting CSV into MySQL.")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="path to the CSV file")
    parser.add_argument("--dataset-name", default=None, help="label stored with each row (default: file name)")
    parser.add_argument("--append", action="store_true", help="do NOT empty the tables first")
    args = parser.parse_args()

    if not args.csv.exists():
        print(f"File not found: {args.csv}")
        print("Download the Kaggle 'Fake Job Postings' CSV and save it as data/fake_job_postings.csv "
              "(see README), or run without --csv to load the small synthetic sample.")
        return 1

    dataset_name = args.dataset_name or args.csv.stem
    print(f"Reading {args.csv} ...")
    raw = read_csv(args.csv)

    conn = get_connection()
    try:
        stats = load_dataframe(conn, raw, dataset_name, replace=not args.append)
    except ValueError as err:
        print(f"Data problem: {err}")
        return 1
    finally:
        conn.close()

    print(f"\nLoaded dataset '{dataset_name}'")
    print(f"  rows in file         : {stats['rows_in']}")
    print(f"  duplicates removed   : {stats['duplicates_removed']}")
    print(f"  rows loaded          : {stats['rows_out']}")
    print(f"  fraudulent postings  : {stats['fraud_rows']}")
    print(f"  salary parsed        : {stats['salary_parsed']}")
    print(f"  signals stored       : {stats['signals_inserted']}")
    print(f"  values shortened     : {stats['values_truncated']}")
    print(f"  flagged (score >= 25): {stats['flagged_at_25']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
