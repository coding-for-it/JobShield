from typing import List, Dict, Any, Tuple


class RiskEngine:
    @classmethod
    def calculate_risk_score(cls, signals: List[Dict[str, Any]]) -> Tuple[int, str, str, List[str]]:
        """
        Calculate deterministic risk score based on detected signals.
        Returns:
            (risk_score, risk_level, verification_status, recommended_actions)
        """
        raw_score = sum(signal.get("score_impact", 0) for signal in signals)
        
        # Clamp score between 0 and 100
        risk_score = max(0, min(100, raw_score))

        # Determine Risk Level
        if risk_score >= 75:
            risk_level = "VERY_HIGH"
        elif risk_score >= 50:
            risk_level = "HIGH"
        elif risk_score >= 25:
            risk_level = "MODERATE"
        else:
            risk_level = "LOW"

        # Determine Verification Status
        critical_count = sum(1 for s in signals if s.get("severity") == "CRITICAL" or s.get("severity") == "HIGH")
        
        if risk_level in ["HIGH", "VERY_HIGH"] or critical_count >= 2:
            verification_status = "VERIFIED_SIGNALS_FOUND"
        elif risk_level == "MODERATE":
            verification_status = "PARTIALLY_VERIFIED"
        elif any(s.get("signal_type") == "UNREACHABLE_WEBSITE" for s in signals):
            verification_status = "INSUFFICIENT_INFORMATION"
        else:
            verification_status = "INCONCLUSIVE"

        # Generate Recommended Actions
        recommended_actions = []
        if any("FEE" in s.get("signal_type", "") or "PAYMENT" in s.get("signal_type", "") for s in signals):
            recommended_actions.append("DO NOT send money, pay registration fees, or transfer cryptocurrency for job placement.")
        if any(s.get("signal_type") == "PERSONAL_EMAIL" for s in signals):
            recommended_actions.append("Contact the company directly through their official website contact page to verify the recruiter's identity.")
        if any(s.get("signal_type") == "DOMAIN_MISMATCH" for s in signals):
            recommended_actions.append("Verify whether the sender domain is an authorized recruiting partner of the parent organization.")
        if any(s.get("signal_type") == "SUSPICIOUS_URL" for s in signals):
            recommended_actions.append("Avoid clicking shortened links or moving communication to unmonitored Telegram/WhatsApp groups.")
        if not recommended_actions:
            recommended_actions.append("Cross-reference the job opening on the company's official careers portal.")

        return risk_score, risk_level, verification_status, recommended_actions
