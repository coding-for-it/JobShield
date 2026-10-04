from typing import List, Dict, Any


class SignalDetector:
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
    def detect_email_signals(cls, email_analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        signals = []

        # 1. Personal Email Provider
        if email_analysis_result.get("is_free_email"):
            signals.append(cls.create_signal(
                signal_type="PERSONAL_EMAIL",
                severity="MEDIUM",
                title="Recruiter Uses Free/Personal Email Domain",
                description="The recruiter sent this offer from a free email provider (e.g. Gmail/Yahoo/Hotmail) rather than an official company domain.",
                evidence=f"Sender Email: {email_analysis_result.get('sender_email')}",
                score_impact=10
            ))

        # 2. Domain Mismatch
        if email_analysis_result.get("domain_mismatch"):
            signals.append(cls.create_signal(
                signal_type="DOMAIN_MISMATCH",
                severity="HIGH",
                title="Recruiter Email Domain Mismatches Company Website",
                description="The recruiter's email domain does not match the company's verified web domain.",
                evidence=f"Sender Domain: {email_analysis_result.get('sender_domain')} vs Company Domain: {email_analysis_result.get('company_domain')}",
                score_impact=15
            ))

        # 3. Payment Request & Specific Fees
        payments = email_analysis_result.get("detected_payments", [])
        if payments:
            for kw in payments:
                if "registration" in kw:
                    signals.append(cls.create_signal(
                        signal_type="REGISTRATION_FEE",
                        severity="CRITICAL",
                        title="Registration Fee Requested",
                        description="Legitimate employers never charge candidates registration fees for job applications.",
                        evidence=f"Detected trigger phrase: '{kw}'",
                        score_impact=25
                    ))
                elif "training" in kw:
                    signals.append(cls.create_signal(
                        signal_type="TRAINING_FEE",
                        severity="CRITICAL",
                        title="Mandatory Paid Training Fee Requested",
                        description="The recruiter requests upfront payment for mandatory training courses.",
                        evidence=f"Detected trigger phrase: '{kw}'",
                        score_impact=20
                    ))
                elif "deposit" in kw:
                    signals.append(cls.create_signal(
                        signal_type="SECURITY_DEPOSIT",
                        severity="CRITICAL",
                        title="Security / Equipment Deposit Requested",
                        description="The recruiter asks for a monetary deposit before sending equipment or commencing work.",
                        evidence=f"Detected trigger phrase: '{kw}'",
                        score_impact=20
                    ))
                else:
                    signals.append(cls.create_signal(
                        signal_type="PAYMENT_REQUEST",
                        severity="CRITICAL",
                        title="Upfront Payment Request Detected",
                        description="The offer mentions monetary payment, transfer, or fee before hiring.",
                        evidence=f"Detected trigger phrase: '{kw}'",
                        score_impact=30
                    ))

        # 4. Urgency
        urgency = email_analysis_result.get("detected_urgency", [])
        if urgency:
            signals.append(cls.create_signal(
                signal_type="URGENT_LANGUAGE",
                severity="MEDIUM",
                title="Suspicious Urgency / Pressure Tactics",
                description="The communication creates artificial time pressure to rush decision making.",
                evidence=f"Detected phrases: {', '.join(urgency)}",
                score_impact=10
            ))

        # 5. Selection without interview
        no_interview = email_analysis_result.get("detected_no_interview", [])
        if no_interview:
            signals.append(cls.create_signal(
                signal_type="NO_INTERVIEW_SELECTION",
                severity="HIGH",
                title="Immediate Job Offer Without Interview",
                description="The candidate was purportedly selected without undergoing standard interview procedures.",
                evidence=f"Detected phrases: {', '.join(no_interview)}",
                score_impact=10
            ))

        # 6. Suspicious Messaging Links
        links = email_analysis_result.get("detected_links", [])
        if links:
            signals.append(cls.create_signal(
                signal_type="SUSPICIOUS_URL",
                severity="HIGH",
                title="Recruitment Redirected to Unofficial Chat Apps",
                description="Communication is directed toward informal messaging channels (Telegram/WhatsApp).",
                evidence=f"Detected channels/patterns: {', '.join(links)}",
                score_impact=15
            ))

        return signals

    @classmethod
    def detect_company_signals(cls, company_analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        signals = []

        # 1. Unreachable website
        if not company_analysis_result.get("reachable"):
            signals.append(cls.create_signal(
                signal_type="UNREACHABLE_WEBSITE",
                severity="HIGH",
                title="Company Website Unreachable",
                description="The company website URL could not be accessed or timed out.",
                evidence=company_analysis_result.get("error") or f"HTTP status code: {company_analysis_result.get('status_code')}",
                score_impact=10
            ))
        else:
            # Website is reachable
            if not company_analysis_result.get("has_careers_page"):
                signals.append(cls.create_signal(
                    signal_type="MISSING_CAREERS_PAGE",
                    severity="LOW",
                    title="No Public Careers / Jobs Section Found",
                    description="The website lacks an easily identifiable careers or job listings page.",
                    evidence=f"Analyzed website: {company_analysis_result.get('website')}",
                    score_impact=5
                ))

            if company_analysis_result.get("has_https"):
                # Positive indicator - reduces risk score
                signals.append(cls.create_signal(
                    signal_type="VERIFIED_COMPANY_DOMAIN",
                    severity="LOW",
                    title="Company Site Uses Secure HTTPS Domain",
                    description="Company website is served over encrypted SSL/TLS protocol.",
                    evidence=f"Secure URL: {company_analysis_result.get('website')}",
                    score_impact=-10
                ))

        return signals
