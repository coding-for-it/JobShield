from typing import Dict, Any
from app.verification.url_checker import extract_domain, get_base_domain


class EmailChecker:
    FREE_EMAIL_DOMAINS = {
        "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com",
        "rediffmail.com", "protonmail.com", "yandex.com", "icloud.com", "live.com"
    }

    PAYMENT_KEYWORDS = [
        "registration fee", "training fee", "security deposit", "laptop fee",
        "processing fee", "onboarding fee", "refundable deposit", "wire transfer",
        "crypto", "bitcoin", "gift card", "send money", "pay before starting"
    ]

    URGENCY_KEYWORDS = [
        "immediate response", "offer expires today", "urgent selection",
        "act fast", "immediate joiner", "urgent placement", "expires in 24 hours"
    ]

    NO_INTERVIEW_KEYWORDS = [
        "selected without interview", "direct selection", "instant selection",
        "no technical round required", "selected based on resume only", "congratulations you are hired"
    ]

    SUSPICIOUS_LINK_PATTERNS = [
        "t.me/", "telegram.me", "wa.me/", "chat.whatsapp.com", "bit.ly/", "tinyurl.com"
    ]

    @classmethod
    def check_email(
        cls,
        sender_email: str,
        subject: str = "",
        body: str = "",
        company_name: str = "",
        company_domain: str | None = None
    ) -> Dict[str, Any]:
        """Analyze recruiter email text and extract risk indicators."""
        content = f"{subject}\n{body}".lower()
        sender_domain = extract_domain(sender_email)
        sender_base_domain = get_base_domain(sender_domain)

        is_free_email = sender_domain in cls.FREE_EMAIL_DOMAINS if sender_domain else False

        domain_mismatch = False
        if company_domain and sender_base_domain and not is_free_email:
            company_base = get_base_domain(extract_domain(company_domain))
            if company_base and company_base != sender_base_domain:
                domain_mismatch = True

        detected_payments = [kw for kw in cls.PAYMENT_KEYWORDS if kw in content]
        detected_urgency = [kw for kw in cls.URGENCY_KEYWORDS if kw in content]
        detected_no_interview = [kw for kw in cls.NO_INTERVIEW_KEYWORDS if kw in content]
        detected_links = [pattern for pattern in cls.SUSPICIOUS_LINK_PATTERNS if pattern in content]

        return {
            "sender_email": sender_email,
            "sender_domain": sender_domain,
            "is_free_email": is_free_email,
            "domain_mismatch": domain_mismatch,
            "company_domain": company_domain,
            "detected_payments": detected_payments,
            "detected_urgency": detected_urgency,
            "detected_no_interview": detected_no_interview,
            "detected_links": detected_links
        }
