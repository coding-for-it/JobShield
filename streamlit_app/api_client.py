import httpx
from typing import Dict, Any, Optional

API_BASE_URL = "http://127.0.0.1:8000/api/v1"


class APIClient:
    @staticmethod
    def _get_headers(token: Optional[str] = None) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    @classmethod
    def register(cls, name: str, email: str, password: str) -> Dict[str, Any]:
        url = f"{API_BASE_URL}/auth/register"
        payload = {"name": name, "email": email, "password": password}
        try:
            response = httpx.post(url, json=payload, timeout=5.0)
            return {"status_code": response.status_code, "data": response.json()}
        except Exception as e:
            return {"status_code": 500, "data": {"error": {"message": str(e)}}}

    @classmethod
    def login(cls, email: str, password: str) -> Dict[str, Any]:
        url = f"{API_BASE_URL}/auth/login"
        payload = {"email": email, "password": password}
        try:
            response = httpx.post(url, json=payload, timeout=5.0)
            return {"status_code": response.status_code, "data": response.json()}
        except Exception as e:
            return {"status_code": 500, "data": {"error": {"message": str(e)}}}

    @classmethod
    def get_me(cls, token: str) -> Dict[str, Any]:
        url = f"{API_BASE_URL}/auth/me"
        try:
            response = httpx.get(url, headers=cls._get_headers(token), timeout=5.0)
            return {"status_code": response.status_code, "data": response.json()}
        except Exception as e:
            return {"status_code": 500, "data": {"error": {"message": str(e)}}}

    @classmethod
    def verify_email(cls, token: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{API_BASE_URL}/verification/email"
        try:
            response = httpx.post(url, json=payload, headers=cls._get_headers(token), timeout=15.0)
            return {"status_code": response.status_code, "data": response.json()}
        except Exception as e:
            return {"status_code": 500, "data": {"error": {"message": str(e)}}}

    @classmethod
    def verify_job(cls, token: str, job_url: str, company_name: Optional[str] = None) -> Dict[str, Any]:
        url = f"{API_BASE_URL}/verification/job"
        payload = {"job_url": job_url, "company_name": company_name}
        try:
            response = httpx.post(url, json=payload, headers=cls._get_headers(token), timeout=15.0)
            return {"status_code": response.status_code, "data": response.json()}
        except Exception as e:
            return {"status_code": 500, "data": {"error": {"message": str(e)}}}

    @classmethod
    def verify_company(cls, token: str, company_name: str, website: str) -> Dict[str, Any]:
        url = f"{API_BASE_URL}/verification/company"
        payload = {"company_name": company_name, "website": website}
        try:
            response = httpx.post(url, json=payload, headers=cls._get_headers(token), timeout=10.0)
            return {"status_code": response.status_code, "data": response.json()}
        except Exception as e:
            return {"status_code": 500, "data": {"error": {"message": str(e)}}}

    @classmethod
    def get_verification_history(cls, token: str) -> Dict[str, Any]:
        url = f"{API_BASE_URL}/verification/history"
        try:
            response = httpx.get(url, headers=cls._get_headers(token), timeout=5.0)
            return {"status_code": response.status_code, "data": response.json()}
        except Exception as e:
            return {"status_code": 500, "data": {"error": {"message": str(e)}}}

    @classmethod
    def list_companies(cls, page: int = 1, limit: int = 10, domain: Optional[str] = None) -> Dict[str, Any]:
        url = f"{API_BASE_URL}/companies?page={page}&limit={limit}"
        if domain:
            url += f"&domain={domain}"
        try:
            response = httpx.get(url, timeout=5.0)
            return {"status_code": response.status_code, "data": response.json()}
        except Exception as e:
            return {"status_code": 500, "data": {"error": {"message": str(e)}}}

    @classmethod
    def create_report(cls, token: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{API_BASE_URL}/reports"
        try:
            response = httpx.post(url, json=payload, headers=cls._get_headers(token), timeout=5.0)
            return {"status_code": response.status_code, "data": response.json()}
        except Exception as e:
            return {"status_code": 500, "data": {"error": {"message": str(e)}}}

    @classmethod
    def list_reports(cls, token: str) -> Dict[str, Any]:
        url = f"{API_BASE_URL}/reports"
        try:
            response = httpx.get(url, headers=cls._get_headers(token), timeout=5.0)
            return {"status_code": response.status_code, "data": response.json()}
        except Exception as e:
            return {"status_code": 500, "data": {"error": {"message": str(e)}}}
