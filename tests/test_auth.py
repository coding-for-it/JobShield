import pytest

def test_register_user_success(client):
    payload = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "password": "SecurePassword123"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "jane@example.com"
    assert data["name"] == "Jane Doe"
    assert "hashed_password" not in data


def test_register_duplicate_email(client):
    payload = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "password": "SecurePassword123"
    }
    client.post("/api/v1/auth/register", json=payload)
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    data = response.json()
    assert data["error"]["code"] == "EMAIL_ALREADY_REGISTERED"


def test_login_success(client):
    register_payload = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "password": "SecurePassword123"
    }
    client.post("/api/v1/auth/register", json=register_payload)

    login_payload = {
        "email": "jane@example.com",
        "password": "SecurePassword123"
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_password(client):
    register_payload = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "password": "SecurePassword123"
    }
    client.post("/api/v1/auth/register", json=register_payload)

    login_payload = {
        "email": "jane@example.com",
        "password": "WrongPassword"
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_protected_endpoint_without_token(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "MISSING_TOKEN"


def test_protected_endpoint_with_valid_token(client, auth_headers):
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testuser@example.com"


def test_protected_endpoint_invalid_token(client):
    headers = {"Authorization": "Bearer invalid_jwt_token_string"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_TOKEN"
