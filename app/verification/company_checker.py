import httpx
from typing import Dict, Any
from app.verification.url_checker import extract_domain, get_base_domain


class CompanyChecker:
    @classmethod
    async def check_company(cls, company_name: str, website: str) -> Dict[str, Any]:
        """Verify company website reachability, HTTPS support, and careers section."""
        if not website:
            return {
                "company_name": company_name,
                "domain": None,
                "reachable": False,
                "has_https": False,
                "status_code": None,
                "reason": "No website URL provided"
            }

        url = website.strip()
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url

        domain = extract_domain(url)
        has_https = url.startswith("https://")
        reachable = False
        status_code = None
        error_msg = None
        has_careers_page = False

        try:
            async with httpx.AsyncClient(timeout=5.0, follow_redirects=True, headers={"User-Agent": "JobShield-Checker/1.0"}) as client:
                response = await client.get(url)
                status_code = response.status_code
                if response.status_code < 400:
                    reachable = True
                    html_content = response.text.lower()
                    if "career" in html_content or "job" in html_content or "join us" in html_content:
                        has_careers_page = True
        except httpx.TimeoutException:
            error_msg = "Connection timed out while reaching company website."
        except Exception as e:
            error_msg = f"Failed to connect to website: {str(e)}"

        return {
            "company_name": company_name,
            "website": url,
            "domain": domain,
            "base_domain": get_base_domain(domain),
            "has_https": has_https,
            "reachable": reachable,
            "status_code": status_code,
            "has_careers_page": has_careers_page,
            "error": error_msg
        }
