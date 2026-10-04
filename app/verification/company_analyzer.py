import httpx
from typing import Dict, Any, Optional
from app.utils.validators import extract_domain, get_base_domain


class CompanyAnalyzer:
    @classmethod
    async def analyze_company(cls, company_name: str, website: str) -> Dict[str, Any]:
        """
        Asynchronously analyze company website reachability, domain, and structure.
        Uses httpx with non-blocking timeout handling so the app never crashes.
        """
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
        has_contact_page = False

        try:
            async with httpx.AsyncClient(timeout=5.0, follow_redirects=True, headers={"User-Agent": "JobShield-Verifier/1.0"}) as client:
                response = await client.get(url)
                status_code = response.status_code
                if response.status_code < 400:
                    reachable = True
                    html_content = response.text.lower()
                    if "career" in html_content or "job" in html_content or "join us" in html_content:
                        has_careers_page = True
                    if "contact" in html_content or "about" in html_content:
                        has_contact_page = True
        except httpx.TimeoutException:
            error_msg = "Connection timed out while reaching company website."
        except httpx.HTTPError as err:
            error_msg = f"HTTP error occurred: {type(err).__name__}"
        except Exception as e:
            error_msg = f"Failed to connect to website: {str(e)}"

        return {
            "company_name": company_name,
            "website": url,
            "domain": domain,
            "base_domain": get_base_domain(domain) if domain else None,
            "has_https": has_https,
            "reachable": reachable,
            "status_code": status_code,
            "has_careers_page": has_careers_page,
            "has_contact_page": has_contact_page,
            "error": error_msg
        }
