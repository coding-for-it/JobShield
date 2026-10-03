def test_create_company(client, auth_headers):
    payload = {
        "name": "Acme Software Corp",
        "website": "https://acme.com",
        "description": "Leading tech company",
        "careers_url": "https://acme.com/careers"
    }
    response = client.post("/api/v1/companies", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Acme Software Corp"
    assert data["domain"] == "acme.com"


def test_get_company(client, auth_headers):
    payload = {"name": "Acme Software Corp", "website": "https://acme.com"}
    res = client.post("/api/v1/companies", json=payload, headers=auth_headers)
    company_id = res.json()["id"]

    response = client.get(f"/api/v1/companies/{company_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Acme Software Corp"


def test_company_not_found(client):
    response = client.get("/api/v1/companies/99999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "COMPANY_NOT_FOUND"


def test_list_companies_pagination(client, auth_headers):
    for i in range(5):
        client.post(
            "/api/v1/companies",
            json={"name": f"Company {i}", "website": f"https://company{i}.com"},
            headers=auth_headers
        )

    response = client.get("/api/v1/companies?page=1&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2
    assert data["pagination"]["total"] == 5
    assert data["pagination"]["total_pages"] == 3


def test_update_company(client, auth_headers):
    res = client.post(
        "/api/v1/companies",
        json={"name": "Old Company Name", "website": "https://old.com"},
        headers=auth_headers
    )
    company_id = res.json()["id"]

    update_res = client.patch(
        f"/api/v1/companies/{company_id}",
        json={"name": "Updated Company Name"},
        headers=auth_headers
    )
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Updated Company Name"


def test_delete_company(client, auth_headers):
    res = client.post(
        "/api/v1/companies",
        json={"name": "To Delete Inc", "website": "https://delete.com"},
        headers=auth_headers
    )
    company_id = res.json()["id"]

    del_res = client.delete(f"/api/v1/companies/{company_id}", headers=auth_headers)
    assert del_res.status_code == 204

    get_res = client.get(f"/api/v1/companies/{company_id}")
    assert get_res.status_code == 404
