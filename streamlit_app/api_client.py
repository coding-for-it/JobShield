import os
import httpx
from typing import Dict, Any, Optional

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api/v1")


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

    # ---------- analytics (read-only) ----------

    @classmethod
    def _analytics_get(cls, token: str, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{API_BASE_URL}/analytics/{path}"
        try:
            response = httpx.get(url, params=params, headers=cls._get_headers(token), timeout=20.0)
            return {"status_code": response.status_code, "data": response.json()}
        except Exception as e:
            return {"status_code": 500, "data": {"error": {"message": str(e)}}}

    @classmethod
    def analytics_summary(cls, token: str, threshold: int = 25) -> Dict[str, Any]:
        return cls._analytics_get(token, "summary", {"threshold": threshold})

    @classmethod
    def analytics_fraud_by(cls, token: str, dimension: str, min_postings: int = 30, limit: int = 15) -> Dict[str, Any]:
        return cls._analytics_get(token, f"fraud-by/{dimension}", {"min_postings": min_postings, "limit": limit})

    @classmethod
    def analytics_features(cls, token: str) -> Dict[str, Any]:
        return cls._analytics_get(token, "features")

    @classmethod
    def analytics_rule_performance(cls, token: str) -> Dict[str, Any]:
        return cls._analytics_get(token, "rule-performance")

    @classmethod
    def analytics_threshold_sweep(cls, token: str) -> Dict[str, Any]:
        return cls._analytics_get(token, "threshold-sweep")
