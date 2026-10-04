"""
Cleaning step of the pipeline (pure pandas, no database).

Input : the raw CSV as a DataFrame (Kaggle "Fake Job Postings" / EMSCAD layout)
Output: a tidy DataFrame + a small dict of numbers describing what was cleaned
"""
import re
from typing import Dict, Optional, Tuple

import pandas as pd

REQUIRED_COLUMNS = ["title", "description", "fraudulent"]

TEXT_COLUMNS = [
    "title", "location", "department", "salary_range", "company_profile",
    "description", "requirements", "benefits", "employment_type",
    "required_experience", "required_education", "industry", "function",
]
FLAG_COLUMNS = ["telecommuting", "has_company_logo", "has_questions"]

_FLAG_WORDS = {"1": 1, "1.0": 1, "true": 1, "t": 1, "yes": 1, "y": 1,
               "0": 0, "0.0": 0, "false": 0, "f": 0, "no": 0, "n": 0}
_SALARY_RE = re.compile(r"^\s*(\d+)\s*-\s*(\d+)\s*$")


def _is_missing(value) -> bool:
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def clean_text(value) -> Optional[str]:
    """Trim spaces; empty strings and NaN become None."""
    if _is_missing(value):
        return None
    text = str(value).strip()
    return text or None


def parse_location(value) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """'US, NY, New York' -> ('US', 'NY', 'New York'). Missing parts become None."""
    text = clean_text(value)
    if not text:
        return None, None, None
    parts = [p.strip() for p in text.split(",")]
    country = parts[0] or None
    if country and len(country) <= 3:
        country = country.upper()
    state = parts[1] if len(parts) > 1 and parts[1] else None
    city = ", ".join(p for p in parts[2:] if p) or None
    return country, state, city


def parse_salary(value) -> Tuple[Optional[int], Optional[int]]:
    """'20000-28000' -> (20000, 28000). Anything else (blank, '0-0', 'Dec-20') -> (None, None)."""
    text = clean_text(value)
    if not text:
        return None, None
    match = _SALARY_RE.match(text)
    if not match:
        return None, None
    low, high = int(match.group(1)), int(match.group(2))
    if (low == 0 and high == 0) or low > high or high > 2_000_000_000:
        return None, None
    return low, high


def _to_flag(series: pd.Series, name: str, strict: bool) -> pd.Series:
    """Turn 0/1/true/false-style values into integers 0 or 1."""
    mapped = series.astype(str).str.strip().str.lower().map(_FLAG_WORDS)
    if strict and mapped.isna().any():
        raise ValueError(f"Column '{name}' has missing or unrecognised values. "
                         "Refusing to guess a label.")
    return mapped.fillna(0).astype(int)


def clean_postings(raw: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """Clean the raw dataset. Returns (clean_dataframe, stats)."""
    df = raw.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing required column(s): {', '.join(missing)}")
    stats = {"rows_in": len(df)}

    # 1. text columns: trim, blank -> None (create the column if the CSV does not have it)
    for col in TEXT_COLUMNS:
        if col not in df.columns:
            df[col] = None
        # list comprehension keeps real None values (Series.map would turn them into NaN)
        df[col] = pd.Series([clean_text(v) for v in df[col]], index=df.index, dtype=object)

    # 2. 0/1 flag columns (the label is strict: we never guess it)
    for col in FLAG_COLUMNS:
        df[col] = _to_flag(df[col], col, strict=False) if col in df.columns else 0
    df["fraudulent"] = _to_flag(df["fraudulent"], "fraudulent", strict=True)

    # 3. job id
    if "job_id" in df.columns:
        ids = pd.to_numeric(df["job_id"], errors="coerce")
        if ids.isna().any():
            raise ValueError("Column 'job_id' has non-numeric values.")
        df["job_id"] = ids.astype(int)
    else:
        df["job_id"] = range(1, len(df) + 1)

    # 4. remove duplicate postings (same content, different job_id)
    content_cols = TEXT_COLUMNS + FLAG_COLUMNS + ["fraudulent"]
    df = df.drop_duplicates(subset=content_cols, keep="first").reset_index(drop=True)
    stats["duplicates_removed"] = stats["rows_in"] - len(df)
    df = df.drop_duplicates(subset=["job_id"], keep="first").reset_index(drop=True)

    # 5. new columns that are easier to analyse
    locations = df["location"].map(parse_location)
    df["country"] = [x[0] for x in locations]
    df["state"] = [x[1] for x in locations]
    df["city"] = [x[2] for x in locations]

    salaries = df["salary_range"].map(parse_salary)
    df["salary_min"] = pd.array([x[0] for x in salaries], dtype="Int64")
    df["salary_max"] = pd.array([x[1] for x in salaries], dtype="Int64")
    df["has_salary"] = df["salary_min"].notna().astype(int)

    df["has_company_profile"] = df["company_profile"].notna().astype(int)
    df["has_requirements"] = df["requirements"].notna().astype(int)
    df["has_benefits"] = df["benefits"].notna().astype(int)
    df["description_length"] = df["description"].map(lambda t: len(t) if isinstance(t, str) else 0).astype(int)

    df = df.rename(columns={"function": "job_function"})

    stats["rows_out"] = len(df)
    stats["fraud_rows"] = int(df["fraudulent"].sum())
    stats["salary_parsed"] = int(df["has_salary"].sum())
    return df, stats
