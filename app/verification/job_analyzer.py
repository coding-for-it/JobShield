import httpx
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
from app.verification.url_analyzer import URLAnalyzer
from app.verification.email_analyzer import EmailAnalyzer
from app.utils.validators import extract_domain, get_base_domain


class JobAnalyzer:
    @classmethod
    async def analyze_job_url(cls, job_url: str) -> Dict[str, Any]:
        """
        Fetch and parse job posting web page.
        Extract title, description, company name, location, and analyze for suspicious signals.
        """
        url_analysis = URLAnalyzer.analyze_url(job_url)
        if not url_analysis["valid"]:
            return {
                "valid": False,
                "url": job_url,
                "error": url_analysis.get("reason", "Invalid job URL format")
            }

        url = url_analysis["url"]
        domain = url_analysis["domain"]

        fetched = False
        status_code = None
        html_title = ""
        meta_description = ""
        page_text = ""
        extracted_company = ""
        extracted_title = ""
        error_msg = None

        try:
            async with httpx.AsyncClient(timeout=6.0, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) JobShield-Verifier/1.0"}) as client:
                response = await client.get(url)
                status_code = response.status_code
                if response.status_code < 400:
                    fetched = True
                    soup = BeautifulSoup(response.text, "html.parser")
                    
                    # Extract title tag
                    if soup.title and soup.title.string:
                        html_title = soup.title.string.strip()
                    
                    # Extract meta description
                    meta_desc_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
                    if meta_desc_tag and meta_desc_tag.get("content"):
                        meta_description = meta_desc_tag["content"].strip()
                    
                    # Extract visible text snippet
                    body = soup.find("body")
                    if body:
                        page_text = body.get_text(separator=" ", strip=True)[:4000]
                    else:
                        page_text = soup.get_text(separator=" ", strip=True)[:4000]

                    # Extract og:site_name for company
                    og_site = soup.find("meta", attrs={"property": "og:site_name"})
                    if og_site and og_site.get("content"):
                        extracted_company = og_site["content"].strip()

                    # Extract og:title for job title
                    og_title = soup.find("meta", attrs={"property": "og:title"})
                    if og_title and og_title.get("content"):
                        extracted_title = og_title["content"].strip()
        except httpx.TimeoutException:
            error_msg = "Request timed out while trying to reach job URL."
        except httpx.HTTPError as e:
            error_msg = f"HTTP request failed: {type(e).__name__}"
        except Exception as ex:
            error_msg = f"Failed to fetch job URL: {str(ex)}"

        combined_text = f"{html_title} {meta_description} {page_text}".lower()

        # Detect payment and urgency keywords in scraped text
        detected_payments = [kw for kw in EmailAnalyzer.PAYMENT_KEYWORDS if kw in combined_text]
        detected_urgency = [kw for kw in EmailAnalyzer.URGENCY_KEYWORDS if kw in combined_text]
        detected_no_interview = [kw for kw in EmailAnalyzer.NO_INTERVIEW_KEYWORDS if kw in combined_text]

        return {
            "valid": True,
            "url": url,
            "domain": domain,
            "base_domain": get_base_domain(domain) if domain else None,
            "fetched": fetched,
            "status_code": status_code,
            "html_title": html_title or extracted_title or "Job Posting",
            "meta_description": meta_description,
            "page_snippet": page_text[:500],
            "extracted_company": extracted_company,
            "extracted_title": extracted_title or html_title,
            "url_analysis": url_analysis,
            "detected_payments": detected_payments,
            "detected_urgency": detected_urgency,
            "detected_no_interview": detected_no_interview,
            "error": error_msg
        }
