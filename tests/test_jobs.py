def test_create_and_get_job(client, auth_headers):
    # 1. Create company first
    comp_res = client.post(
        "/api/v1/companies",
        json={"name": "Tech Corp", "website": "https://techcorp.com"},
        headers=auth_headers
    )
    company_id = comp_res.json()["id"]

    # 2. Create job
    job_payload = {
        "company_id": company_id,
        "title": "FastAPI Developer",
        "description": "Develop Python APIs",
        "location": "Remote",
        "salary_text": "$90,000"
    }
    job_res = client.post("/api/v1/jobs", json=job_payload, headers=auth_headers)
    assert job_res.status_code == 201
    job_data = job_res.json()
    assert job_data["title"] == "FastAPI Developer"
    assert job_data["company_id"] == company_id

    # 3. Get job details
    get_res = client.get(f"/api/v1/jobs/{job_data['id']}")
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "FastAPI Developer"


def test_list_jobs_filtering(client, auth_headers):
    comp_res = client.post(
        "/api/v1/companies",
        json={"name": "Global Tech", "website": "https://global.com"},
        headers=auth_headers
    )
    company_id = comp_res.json()["id"]

    client.post(
        "/api/v1/jobs",
        json={"company_id": company_id, "title": "Data Analyst", "location": "New York"},
        headers=auth_headers
    )
    client.post(
        "/api/v1/jobs",
        json={"company_id": company_id, "title": "Backend Engineer", "location": "Remote"},
        headers=auth_headers
    )

    # Filter by location
    res = client.get("/api/v1/jobs?location=Remote")
    assert res.status_code == 200
    data = res.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["title"] == "Backend Engineer"
