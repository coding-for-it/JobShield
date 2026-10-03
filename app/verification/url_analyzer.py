import re
from typing import Dict, Any, List
from urllib.parse import urlparse
from app.utils.validators import extract_domain, get_base_domain


class URLAnalyzer:
    SUSPICIOUS_KEYWORDS = [
        "login-verify", "account-update", "secure-job", "free-job",
        "quick-money", "earn-daily", "payment-fee", "registration-fee",
        "telegram", "t.me", "wa.me", "whatsapp"
    ]

    @classmethod
    def analyze_url(cls, url: str, expected_company_domain: str | None = None) -> Dict[str, Any]:
        """
        Analyze a URL for security and verification signals.
        Returns a dictionary containing raw detection flags.
        """
        if not url:
            return {"valid": False, "reason": "Empty URL provided"}

        url_str = url.strip()
        if not url_str.startswith("http://") and not url_str.startswith("https://"):
            url_str = "https://" + url_str

        try:
            parsed = urlparse(url_str)
        except Exception as e:
            return {"valid": False, "reason": f"Invalid URL structure: {str(e)}"}

        hostname = parsed.netloc.split(":")[0] if parsed.netloc else ""
        is_https = parsed.scheme == "https"
        is_ip_address = bool(re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", hostname))
        
        domain = extract_domain(url_str)
        base_domain = get_base_domain(domain) if domain else None

        # Check subdomains depth
        subdomains_count = len(hostname.split(".")) - 2 if hostname and not is_ip_address else 0
        excessive_subdomains = subdomains_count > 2

        # Check length
        is_excessive_length = len(url_str) > 120

        # Check suspicious keywords in path or hostname
        found_keywords = [kw for kw in cls.SUSPICIOUS_KEYWORDS if kw in url_str.lower()]

        # Check domain mismatch if expected company domain provided
        domain_mismatch = False
        if expected_company_domain and base_domain:
            expected_base = get_base_domain(expected_company_domain)
            if expected_base and expected_base != base_domain:
                domain_mismatch = True

        return {
            "valid": True,
            "url": url_str,
            "hostname": hostname,
            "domain": domain,
            "base_domain": base_domain,
            "is_https": is_https,
            "is_ip_address": is_ip_address,
            "excessive_subdomains": excessive_subdomains,
            "is_excessive_length": is_excessive_length,
            "found_keywords": found_keywords,
            "domain_mismatch": domain_mismatch,
            "expected_company_domain": expected_company_domain
        }
