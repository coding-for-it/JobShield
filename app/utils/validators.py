import re
from typing import Optional
from urllib.parse import urlparse


def extract_domain(url_or_email: str) -> Optional[str]:
    """
    Extract clean domain from a URL string or email address.
    Example: 'https://careers.google.com/jobs' -> 'google.com'
    Example: 'recruiter@microsoft.com' -> 'microsoft.com'
    """
    if not url_or_email:
        return None

    value = url_or_email.strip().lower()

    # If email address
    if "@" in value and not value.startswith("http://") and not value.startswith("https://"):
        parts = value.split("@")
        if len(parts) == 2:
            return parts[1].strip()

    # If URL
    if not value.startswith("http://") and not value.startswith("https://"):
        value = "https://" + value

    try:
        parsed = urlparse(value)
        hostname = parsed.netloc or parsed.path
        if ":" in hostname:
            hostname = hostname.split(":")[0]

        # Strip www.
        if hostname.startswith("www."):
            hostname = hostname[4:]

        return hostname if hostname else None
    except Exception:
        return None


def get_base_domain(domain: str) -> Optional[str]:
    """
    Extract base domain (e.g. 'sub.example.co.uk' -> 'example.co.uk' or 'sub.google.com' -> 'google.com')
    """
    if not domain:
        return None
    domain = domain.lower().strip()
    parts = domain.split(".")
    if len(parts) <= 2:
        return domain
    return ".".join(parts[-2:])
