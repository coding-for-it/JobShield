def test_create_and_list_reports(client, auth_headers):
    report_payload = {
        "report_type": "PAYMENT_REQUEST",
        "description": "Recruiter asked for $100 registration deposit via gift cards."
    }
    create_res = client.post("/api/v1/reports", json=report_payload, headers=auth_headers)
    assert create_res.status_code == 201
    report_data = create_res.json()
    assert report_data["report_type"] == "PAYMENT_REQUEST"
    assert report_data["status"] == "PENDING"

    # List reports
    list_res = client.get("/api/v1/reports", headers=auth_headers)
    assert list_res.status_code == 200
    reports = list_res.json()
    assert len(reports) == 1
    assert reports[0]["id"] == report_data["id"]


def test_report_unauthenticated_forbidden(client):
    report_payload = {
        "report_type": "FAKE_OFFER",
        "description": "Unauthenticated test report"
    }
    res = client.post("/api/v1/reports", json=report_payload)
    assert res.status_code == 401
