"""
Analytics tests use a small dataset built by hand, so every expected number can be checked
with a pencil:

    4 fake postings with a 'registration fee' + nothing filled in   -> score 45  (caught)
    2 fake postings with plain text + nothing filled in             -> score 20  (missed at threshold 25)
    1 real posting that mentions 'crypto'                           -> score 30  (false alarm)
   13 real, clean, complete postings                                -> score 0

    total 20, fake 6 (30%).  At threshold 25: TP=4  FP=1  FN=2  TN=13
    precision = 4/5 = 80%     recall = 4/6 = 66.67%     accuracy = 17/20 = 85%
"""
import pandas as pd
import pytest

from app.database import get_connection
from etl.load_postings import load_dataframe

H = "/api/v1/analytics"


def _row(job_id, title, description, fraud, complete, employment_type, industry):
    return {
        "job_id": job_id, "title": title, "location": "US, CA, Fresno", "salary_range": "",
        "company_profile": "A real company." if complete else "",
        "description": description, "requirements": "", "benefits": "",
        "telecommuting": 0, "has_company_logo": int(complete), "has_questions": int(complete),
        "employment_type": employment_type, "required_experience": "", "required_education": "",
        "industry": industry, "function": "", "fraudulent": fraud,
    }


@pytest.fixture
def loaded():
    rows, jid = [], 0
    for i in range(4):
        jid += 1
        rows.append(_row(jid, f"Fee job {i}", f"Pay a registration fee of 100 to start. Ref {i}", 1, False, "Part-time", "Retail"))
    for i in range(2):
        jid += 1
        rows.append(_row(jid, f"Quiet fake {i}", f"Easy work, apply now. Ref {i}", 1, False, "Contract", "Retail"))
    jid += 1
    rows.append(_row(jid, "Blockchain dev", "Build a crypto exchange backend.", 0, True, "Full-time", "IT"))
    for i in range(13):
        jid += 1
        rows.append(_row(jid, f"Analyst {i}", f"Build internal dashboards. Ref {i}", 0, True, "Full-time", "IT"))
    conn = get_connection()
    try:
        stats = load_dataframe(conn, pd.DataFrame(rows), "unit_test_dataset")
    finally:
        conn.close()
    return stats


def test_loader_reports_counts(loaded):
    assert loaded["rows_out"] == 20 and loaded["fraud_rows"] == 6
    assert loaded["flagged_at_25"] == 5


def test_loader_replaces_previous_data(loaded, client, auth_headers):
    conn = get_connection()
    try:
        load_dataframe(conn, pd.DataFrame([_row(1, "Only one", "text", 0, True, "Full-time", "IT")]), "second")
    finally:
        conn.close()
    data = client.get(f"{H}/summary", headers=auth_headers).json()
    assert data["total_postings"] == 1 and data["datasets"] == ["second"]


def test_summary_metrics_are_exact(loaded, client, auth_headers):
    data = client.get(f"{H}/summary?threshold=25", headers=auth_headers).json()
    assert data["datasets"] == ["unit_test_dataset"]
    assert data["total_postings"] == 20 and data["fraud_postings"] == 6
    assert data["fraud_rate_pct"] == 30.0
    assert data["confusion_matrix"] == {"true_positives": 4, "false_positives": 1,
                                        "false_negatives": 2, "true_negatives": 13}
    assert data["precision_pct"] == 80.0
    assert data["recall_pct"] == 66.67
    assert data["accuracy_pct"] == 85.0
    assert data["always_real_accuracy_pct"] == 70.0


def test_summary_with_no_flags_gives_null_precision(loaded, client, auth_headers):
    data = client.get(f"{H}/summary?threshold=100", headers=auth_headers).json()
    assert data["precision_pct"] is None      # nothing flagged: precision is undefined, not 0
    assert data["recall_pct"] == 0.0


def test_summary_on_empty_database(client, auth_headers):
    data = client.get(f"{H}/summary", headers=auth_headers).json()
    assert data["total_postings"] == 0 and data["fraud_rate_pct"] is None and data["datasets"] == []


def test_fraud_by_employment_type_ranks_groups(loaded, client, auth_headers):
    rows = client.get(f"{H}/fraud-by/employment_type?min_postings=1", headers=auth_headers).json()
    by_cat = {r["category"]: r for r in rows}
    assert by_cat["Part-time"]["postings"] == 4 and by_cat["Part-time"]["fraud_pct"] == 100.0
    assert by_cat["Contract"]["fraud_pct"] == 100.0
    assert by_cat["Full-time"]["postings"] == 14 and by_cat["Full-time"]["fraud_pct"] == 0.0
    assert by_cat["Full-time"]["fraud_rank"] == 3


def test_fraud_by_min_postings_hides_small_groups(loaded, client, auth_headers):
    rows = client.get(f"{H}/fraud-by/employment_type?min_postings=5", headers=auth_headers).json()
    assert [r["category"] for r in rows] == ["Full-time"]


def test_fraud_by_rejects_unknown_column(loaded, client, auth_headers):
    for bad in ["hashed_password", "id;DROP TABLE users", "description"]:
        assert client.get(f"{H}/fraud-by/{bad}", headers=auth_headers).status_code == 422


def test_features_compare_present_vs_absent(loaded, client, auth_headers):
    rows = client.get(f"{H}/features", headers=auth_headers).json()
    logo = {r["feature_value"]: r for r in rows if r["feature"] == "has_company_logo"}
    assert logo[0]["postings"] == 6 and logo[0]["fraud_pct"] == 100.0
    assert logo[1]["postings"] == 14 and logo[1]["fraud_pct"] == 0.0


def test_rule_performance_is_per_rule(loaded, client, auth_headers):
    rules = {r["signal_type"]: r for r in client.get(f"{H}/rule-performance", headers=auth_headers).json()}
    fee = rules["REGISTRATION_FEE"]
    assert fee["postings_flagged"] == 4 and fee["precision_pct"] == 100.0 and fee["coverage_pct"] == 66.67
    crypto = rules["PAYMENT_REQUEST"]                  # the false alarm
    assert crypto["postings_flagged"] == 1 and crypto["precision_pct"] == 0.0
    assert rules["NO_COMPANY_PROFILE"]["postings_flagged"] == 6
    assert rules["NO_COMPANY_PROFILE"]["coverage_pct"] == 100.0


def test_threshold_sweep_precision_recall_tradeoff(loaded, client, auth_headers):
    sweep = {r["threshold"]: r for r in client.get(f"{H}/threshold-sweep", headers=auth_headers).json()}
    assert sweep[10]["flagged"] == 7 and sweep[10]["precision_pct"] == 85.71 and sweep[10]["recall_pct"] == 100.0
    assert sweep[25]["precision_pct"] == 80.0 and sweep[25]["recall_pct"] == 66.67
    assert sweep[50]["flagged"] == 0 and sweep[50]["precision_pct"] is None and sweep[50]["recall_pct"] == 0.0


@pytest.mark.parametrize("path", ["/summary", "/features", "/rule-performance", "/threshold-sweep",
                                  "/fraud-by/industry"])
def test_analytics_requires_login(client, path):
    assert client.get(f"{H}{path}").status_code == 401


def test_threshold_out_of_range_is_rejected(client, auth_headers):
    assert client.get(f"{H}/summary?threshold=500", headers=auth_headers).status_code == 422


def test_loader_shortens_values_that_are_too_long_for_their_column():
    # Regression: one real posting lists dozens of cities, longer than the city column.
    row = _row(1, "Long location", "Plain text.", 0, True, "Full-time", "IT")
    row["location"] = "US, CA, " + ", ".join(f"City{i}" for i in range(200))
    conn = get_connection()
    try:
        stats = load_dataframe(conn, pd.DataFrame([row]), "long_values")
    finally:
        conn.close()
    assert stats["rows_out"] == 1 and stats["values_truncated"] == 1
