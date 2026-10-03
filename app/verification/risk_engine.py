from typing import List, Dict, Any, Tuple


class RiskEngine:
    @classmethod
    def create_signal(
        cls,
        signal_type: str,
        severity: str,
        title: str,
        description: str,
        evidence: str,
        score_impact: int
    ) -> Dict[str, Any]:
        return {
            "signal_type": signal_type,
            "severity": severity,  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
            "title": title,
            "description": description,
            "evidence": evidence,
            "score_impact": score_impact
        }

    @classmethod
    def evaluate_email_signals(cls, email_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        signals = []

        if email_result.get("is_free_email"):
            signals.append(cls.create_signal(
                signal_type="PERSONAL_EMAIL",
                severity="MEDIUM",
                title="Recruiter Uses Free/Personal Email Domain",
                description="The recruiter sent this offer from a free email provider (e.g. Gmail/Yahoo/Hotmail) rather than an official company domain.",
                evidence=f"Sender Email: {email_result.get('sender_email')}",
                score_impact=10
            ))

        if email_result.get("domain_mismatch"):
            signals.append(cls.create_signal(
                signal_type="DOMAIN_MISMATCH",
                severity="HIGH",
                title="Recruiter Email Domain Mismatches Company Website",
                description="The recruiter's email domain does not match the company's verified web domain.",
                evidence=f"Sender Domain: {email_result.get('sender_domain')} vs Company Domain: {email_result.get('company_domain')}",
                score_impact=15
            ))

        for kw in email_result.get("detected_payments", []):
            if "registration" in kw:
                signals.append(cls.create_signal(
                    signal_type="REGISTRATION_FEE",
                    severity="CRITICAL",
                    title="Registration Fee Requested",
                    description="Legitimate employers never charge candidates registration fees for job applications.",
                    evidence=f"Trigger phrase: '{kw}'",
                    score_impact=25
                ))
            elif "training" in kw:
                signals.append(cls.create_signal(
                    signal_type="TRAINING_FEE",
                    severity="CRITICAL",
                    title="Mandatory Paid Training Fee Requested",
                    description="The recruiter requests upfront payment for mandatory training courses.",
                    evidence=f"Trigger phrase: '{kw}'",
                    score_impact=20
                ))
            elif "deposit" in kw:
                signals.append(cls.create_signal(
                    signal_type="SECURITY_DEPOSIT",
                    severity="CRITICAL",
                    title="Security / Equipment Deposit Requested",
                    description="The recruiter asks for a monetary deposit before sending equipment.",
                    evidence=f"Trigger phrase: '{kw}'",
                    score_impact=20
                ))
            else:
                signals.append(cls.create_signal(
                    signal_type="PAYMENT_REQUEST",
                    severity="CRITICAL",
                    title="Upfront Payment Request Detected",
                    description="The offer mentions monetary payment, transfer, or fee before hiring.",
                    evidence=f"Trigger phrase: '{kw}'",
                    score_impact=30
                ))

        if email_result.get("detected_urgency"):
            signals.append(cls.create_signal(
                signal_type="URGENT_LANGUAGE",
                severity="MEDIUM",
                title="Suspicious Urgency / Pressure Tactics",
                description="The communication creates artificial time pressure to rush decision making.",
                evidence=f"Phrases: {', '.join(email_result['detected_urgency'])}",
                score_impact=10
            ))

        if email_result.get("detected_no_interview"):
            signals.append(cls.create_signal(
                signal_type="NO_INTERVIEW_SELECTION",
                severity="HIGH",
                title="Immediate Job Offer Without Interview",
                description="The candidate was selected without undergoing standard interview procedures.",
                evidence=f"Phrases: {', '.join(email_result['detected_no_interview'])}",
                score_impact=10
            ))

        if email_result.get("detected_links"):
            signals.append(cls.create_signal(
                signal_type="SUSPICIOUS_URL",
                severity="HIGH",
                title="Recruitment Redirected to Chat Apps",
                description="Communication is directed toward informal messaging channels (Telegram/WhatsApp).",
                evidence=f"Channels: {', '.join(email_result['detected_links'])}",
                score_impact=15
            ))

        return signals

    @classmethod
    def evaluate_company_signals(cls, company_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        signals = []
        if not company_result.get("reachable"):
            signals.append(cls.create_signal(
                signal_type="UNREACHABLE_WEBSITE",
                severity="HIGH",
                title="Company Website Unreachable",
                description="The company website URL could not be accessed.",
                evidence=company_result.get("error", "Website connection failed"),
                score_impact=10
            ))
        else:
            if not company_result.get("has_careers_page"):
                signals.append(cls.create_signal(
                    signal_type="MISSING_CAREERS_PAGE",
                    severity="LOW",
                    title="No Public Careers Section Found",
                    description="The website lacks an easily identifiable careers page.",
                    evidence=f"Website: {company_result.get('website')}",
                    score_impact=5
                ))

            if company_result.get("has_https"):
                signals.append(cls.create_signal(
                    signal_type="VERIFIED_COMPANY_DOMAIN",
                    severity="LOW",
                    title="Company Site Uses Secure HTTPS Domain",
                    description="Company website is served over encrypted SSL/TLS protocol.",
                    evidence=f"URL: {company_result.get('website')}",
                    score_impact=-10
                ))
        return signals

    @classmethod
    def calculate_risk_score(cls, signals: List[Dict[str, Any]]) -> Tuple[int, str, str, List[str]]:
        raw_score = sum(s.get("score_impact", 0) for s in signals)
        risk_score = max(0, min(100, raw_score))

        if risk_score >= 75:
            risk_level = "VERY_HIGH"
        elif risk_score >= 50:
            risk_level = "HIGH"
        elif risk_score >= 25:
            risk_level = "MODERATE"
        else:
            risk_level = "LOW"

        critical_count = sum(1 for s in signals if s.get("severity") in ["CRITICAL", "HIGH"])
        if risk_level in ["HIGH", "VERY_HIGH"] or critical_count >= 2:
            verification_status = "VERIFIED_SIGNALS_FOUND"
        elif risk_level == "MODERATE":
            verification_status = "PARTIALLY_VERIFIED"
        elif any(s.get("signal_type") == "UNREACHABLE_WEBSITE" for s in signals):
            verification_status = "INSUFFICIENT_INFORMATION"
        else:
            verification_status = "INCONCLUSIVE"

        actions = []
        if any("FEE" in s.get("signal_type", "") or "PAYMENT" in s.get("signal_type", "") for s in signals):
            actions.append("DO NOT send money, pay registration fees, or transfer gift cards for job placement.")
        if any(s.get("signal_type") == "PERSONAL_EMAIL" for s in signals):
            actions.append("Contact the company directly through their official website contact page to verify the recruiter.")
        if any(s.get("signal_type") == "DOMAIN_MISMATCH" for s in signals):
            actions.append("Verify whether the sender domain is an authorized recruiting partner of the company.")
        if not actions:
            actions.append("Cross-reference the job opening on the company's official careers portal.")

        return risk_score, risk_level, verification_status, actions
