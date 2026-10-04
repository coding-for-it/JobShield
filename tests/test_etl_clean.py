import pandas as pd
import pytest

from etl.clean import clean_postings, parse_location, parse_salary


def test_parse_location_splits_country_state_city():
    assert parse_location("US, NY, New York") == ("US", "NY", "New York")


def test_parse_location_handles_missing_parts():
    assert parse_location("GB, , London") == ("GB", None, "London")
    assert parse_location("us") == ("US", None, None)
    assert parse_location(None) == (None, None, None)
    assert parse_location("") == (None, None, None)


def test_parse_salary_valid_and_junk_values():
    assert parse_salary("20000-28000") == (20000, 28000)
    assert parse_salary(" 100 - 200 ") == (100, 200)
    # unknown, zero, date-like (a known spreadsheet corruption) and reversed ranges -> no salary
    for junk in ["0-0", "Dec-20", "", None, "negotiable", "50000-20000"]:
        assert parse_salary(junk) == (None, None)


def _raw(**overrides):
    base = {"job_id": 1, "title": " Data Analyst ", "description": "Build reports.", "fraudulent": 0,
            "location": "US, CA, Fresno", "salary_range": "10-20", "company_profile": "",
            "telecommuting": 1, "has_company_logo": "1", "has_questions": 0, "function": "IT"}
    base.update(overrides)
    return base


def test_clean_postings_basic_fields():
    df, stats = clean_postings(pd.DataFrame([_raw()]))
    row = df.iloc[0]
    assert row["title"] == "Data Analyst"              # trimmed
    assert row["country"] == "US" and row["city"] == "Fresno"
    assert row["salary_min"] == 10 and row["has_salary"] == 1
    assert row["has_company_profile"] == 0             # empty string counted as missing
    assert row["has_company_logo"] == 1 and row["telecommuting"] == 1
    assert row["job_function"] == "IT"                 # "function" renamed
    assert row["description_length"] == len("Build reports.")
    assert stats["rows_in"] == 1 and stats["rows_out"] == 1


def test_clean_postings_removes_duplicates_with_different_ids():
    raw = pd.DataFrame([_raw(job_id=1), _raw(job_id=2), _raw(job_id=3, title="Other")])
    df, stats = clean_postings(raw)
    assert len(df) == 2
    assert stats["duplicates_removed"] == 1


def test_clean_postings_missing_required_column():
    with pytest.raises(ValueError, match="description"):
        clean_postings(pd.DataFrame([{"title": "x", "fraudulent": 0}]))


def test_clean_postings_refuses_to_guess_a_bad_label():
    with pytest.raises(ValueError, match="fraudulent"):
        clean_postings(pd.DataFrame([_raw(fraudulent="maybe")]))


def test_clean_postings_creates_job_id_when_absent():
    raw = pd.DataFrame([{"title": "A", "description": "x", "fraudulent": 0},
                        {"title": "B", "description": "y", "fraudulent": 1}])
    df, _ = clean_postings(raw)
    assert list(df["job_id"]) == [1, 2]


def test_clean_postings_handles_missing_descriptions_and_text_fields():
    # Regression: the real Kaggle file has empty descriptions (read by pandas as NaN).
    import numpy as np
    raw = pd.DataFrame([
        {"job_id": 1, "title": "No text at all", "description": np.nan, "requirements": np.nan,
         "company_profile": np.nan, "fraudulent": 1},
        {"job_id": 2, "title": "Has text", "description": "Some text", "fraudulent": 0},
    ])
    df, _ = clean_postings(raw)
    first = df[df["job_id"] == 1].iloc[0]
    assert first["description"] is None and first["description_length"] == 0
    assert first["has_company_profile"] == 0
