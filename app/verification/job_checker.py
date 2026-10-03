import httpx
from bs4 import BeautifulSoup
from typing import Dict, Any
from app.verification.url_checker import URLChecker, extract_domain, get_base_domain
from app.verification.email_checker import EmailChecker


class JobChecker:
    @classmethod
    async def check_job(cls, job_url: str) -> Dict[str, Any]:
        """Fetch and scrape job posting web page for fee demands and suspicious keywords."""
        url_analysis = URLChecker.check_url(job_url)
        if not url_analysis["valid"]:
            return {
                "valid": False,
                "url": job_url,
                "error": url_analysis.get("reason", "Invalid URL")
            }

        url = url_analysis["url"]
        domain = url_analysis["domain"]

        fetched = False
        status_code = None
        html_title = ""
        meta_description = ""
        page_text = ""
        error_msg = None

        try:
            async with httpx.AsyncClient(timeout=6.0, follow_redirects=True, headers={"User-Agent": "JobShield-Checker/1.0"}) as client:
                response = await client.get(url)
                status_code = response.status_code
                if response.status_code < 400:
                    fetched = True
                    soup = BeautifulSoup(response.text, "html.parser")
                    if soup.title and soup.title.string:
                        html_title = soup.title.string.strip()
                    meta_desc = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
                    if meta_desc and meta_desc.get("content"):
                        meta_description = meta_desc["content"].strip()
                    page_text = soup.get_text(separator=" ", strip=True)[:3000]
        except httpx.TimeoutException:
            error_msg = "Connection timed out fetching job page."
        except Exception as e:
            error_msg = f"Failed to fetch job page: {str(e)}"

        combined_text = f"{html_title} {meta_description} {page_text}".lower()

        detected_payments = [kw for kw in EmailChecker.PAYMENT_KEYWORDS if kw in combined_text]
        detected_urgency = [kw for kw in EmailChecker.URGENCY_KEYWORDS if kw in combined_text]

        return {
            "valid": True,
            "url": url,
            "domain": domain,
            "base_domain": get_base_domain(domain),
            "fetched": fetched,
            "status_code": status_code,
            "html_title": html_title or "Job Posting",
            "meta_description": meta_description,
            "url_analysis": url_analysis,
            "detected_payments": detected_payments,
            "detected_urgency": detected_urgency,
            "error": error_msg
        }
