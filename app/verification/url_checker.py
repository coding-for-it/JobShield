import re
from typing import Dict, Any
from urllib.parse import urlparse


def extract_domain(url_or_email: str) -> str | None:
    """Extract domain from URL or email address."""
    if not url_or_email:
        return None
    val = url_or_email.strip().lower()

    if "@" in val and not val.startswith("http://") and not val.startswith("https://"):
        return val.split("@")[-1].strip()

    if not val.startswith("http://") and not val.startswith("https://"):
        val = "https://" + val

    try:
        parsed = urlparse(val)
        host = parsed.netloc.split(":")[0] if parsed.netloc else parsed.path.split("/")[0]
        if host.startswith("www."):
            host = host[4:]
        return host if host else None
    except Exception:
        return None


def get_base_domain(domain: str | None) -> str | None:
    """Get root domain (e.g. sub.example.com -> example.com)."""
    if not domain:
        return None
    parts = domain.lower().strip().split(".")
    if len(parts) <= 2:
        return domain
    return ".".join(parts[-2:])


class URLChecker:
    SUSPICIOUS_KEYWORDS = [
        "login-verify", "secure-job", "free-job", "earn-daily",
        "payment-fee", "registration-fee", "telegram", "t.me", "wa.me", "whatsapp"
    ]

    @classmethod
    def check_url(cls, url: str, expected_domain: str | None = None) -> Dict[str, Any]:
        """Analyze URL structure and security properties."""
        if not url:
            return {"valid": False, "reason": "Empty URL"}

        url_str = url.strip()
        if not url_str.startswith("http://") and not url_str.startswith("https://"):
            url_str = "https://" + url_str

        try:
            parsed = urlparse(url_str)
        except Exception as e:
            return {"valid": False, "reason": f"Invalid URL: {str(e)}"}

        hostname = parsed.netloc.split(":")[0] if parsed.netloc else ""
        is_https = parsed.scheme == "https"
        is_ip_address = bool(re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", hostname))
        
        domain = extract_domain(url_str)
        base_domain = get_base_domain(domain)

        subdomains_count = len(hostname.split(".")) - 2 if hostname and not is_ip_address else 0
        excessive_subdomains = subdomains_count > 2
        is_excessive_length = len(url_str) > 120

        found_keywords = [kw for kw in cls.SUSPICIOUS_KEYWORDS if kw in url_str.lower()]

        domain_mismatch = False
        if expected_domain and base_domain:
            expected_base = get_base_domain(extract_domain(expected_domain))
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
            "domain_mismatch": domain_mismatch
        }
