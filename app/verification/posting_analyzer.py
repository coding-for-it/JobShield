from typing import Any, Dict, List
from app.verification.email_analyzer import EmailAnalyzer
from app.verification.signal_detector import SignalDetector


class PostingAnalyzer:
    """
    Applies the scam rules to one job posting from the analysis dataset.

    Two groups of rules:
      1. TEXT rules      - the SAME keyword lists the email check uses (fees, urgency,
                           "no interview", Telegram/WhatsApp links). Reused, not copied.
      2. STRUCTURE rules - things missing from the posting itself (no company profile,
                           no logo, no screening questions).

    The weights below are my first guesses, written BEFORE looking at the data.
    The analysis (sql/analysis/) measures whether each rule actually helps.
    """

    # signal_type -> (severity, score, title, what it means)
    STRUCTURE_RULES = {
        "NO_COMPANY_PROFILE": ("MEDIUM", 10, "Posting Has No Company Profile",
                               "The posting does not describe the hiring company."),
        "NO_COMPANY_LOGO": ("LOW", 5, "Posting Has No Company Logo",
                            "No company logo is attached to the posting."),
        "NO_SCREENING_QUESTIONS": ("LOW", 5, "Posting Has No Screening Questions",
                                   "Applicants are not asked any screening questions."),
    }
    STRUCTURE_SIGNAL_TYPES = tuple(STRUCTURE_RULES)

    @staticmethod
    def build_text(posting: Dict[str, Any]) -> str:
        """Join the text fields of a posting into one lowercase string to search."""
        parts = [posting.get("title"), posting.get("description"),
                 posting.get("requirements"), posting.get("benefits")]
        return " ".join(p for p in parts if isinstance(p, str)).lower()

    @classmethod
    def text_signals(cls, posting: Dict[str, Any]) -> List[Dict[str, Any]]:
        text = cls.build_text(posting)
        facts = {
            # the sender-related facts do not apply to a posting
            "sender_email": None, "sender_domain": None, "company_domain": None,
            "is_free_email": False, "domain_mismatch": False,
            "detected_payments": [k for k in EmailAnalyzer.PAYMENT_KEYWORDS if k in text],
            "detected_urgency": [k for k in EmailAnalyzer.URGENCY_KEYWORDS if k in text],
            "detected_no_interview": [k for k in EmailAnalyzer.NO_INTERVIEW_KEYWORDS if k in text],
            "detected_links": [p for p in EmailAnalyzer.SUSPICIOUS_LINK_PATTERNS if p in text],
        }
        return SignalDetector.detect_email_signals(facts)

    @classmethod
    def structure_signals(cls, posting: Dict[str, Any]) -> List[Dict[str, Any]]:
        checks = {
            "NO_COMPANY_PROFILE": not posting.get("has_company_profile"),
            "NO_COMPANY_LOGO": not posting.get("has_company_logo"),
            "NO_SCREENING_QUESTIONS": not posting.get("has_questions"),
        }
        signals = []
        for signal_type, missing in checks.items():
            if missing:
                severity, score, title, description = cls.STRUCTURE_RULES[signal_type]
                signals.append(SignalDetector.create_signal(
                    signal_type=signal_type, severity=severity, title=title,
                    description=description, evidence="Field is empty in the posting",
                    score_impact=score,
                ))
        return signals

    @classmethod
    def analyze(cls, posting: Dict[str, Any]) -> List[Dict[str, Any]]:
        """All signals (text rules + structure rules) for one posting."""
        return cls.text_signals(posting) + cls.structure_signals(posting)
