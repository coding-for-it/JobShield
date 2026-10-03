import re
from typing import Dict, Any, List
from app.utils.validators import extract_domain, get_base_domain


class EmailAnalyzer:
    FREE_EMAIL_DOMAINS = {
        "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com",
        "rediffmail.com", "protonmail.com", "yandex.com", "icloud.com", "live.com", "mail.com"
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
    def analyze_email(
        cls,
        sender_email: str,
        subject: str = "",
        body: str = "",
        company_name: str = "",
        company_domain: str | None = None
    ) -> Dict[str, Any]:
        """
        Analyze a recruiter email message and extract suspicious signals.
        """
        content = f"{subject}\n{body}".lower()
        sender_domain = extract_domain(sender_email)
        sender_base_domain = get_base_domain(sender_domain) if sender_domain else None

        # 1. Check if sender is using a personal/free email provider
        is_free_email = sender_domain in cls.FREE_EMAIL_DOMAINS if sender_domain else False

        # 2. Check domain mismatch with company domain
        domain_mismatch = False
        if company_domain and sender_base_domain and not is_free_email:
            company_base = get_base_domain(company_domain)
            if company_base and company_base != sender_base_domain:
                domain_mismatch = True

        # 3. Detect payment requests
        detected_payments = [kw for kw in cls.PAYMENT_KEYWORDS if kw in content]

        # 4. Detect urgency terms
        detected_urgency = [kw for kw in cls.URGENCY_KEYWORDS if kw in content]

        # 5. Detect selection without interview
        detected_no_interview = [kw for kw in cls.NO_INTERVIEW_KEYWORDS if kw in content]

        # 6. Detect suspicious contact channels (Telegram/WhatsApp/URL shorteners)
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
