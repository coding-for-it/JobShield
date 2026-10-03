from typing import Dict, Any, List
from app.database import execute_query, fetch_one, fetch_all
from app.verification.email_checker import EmailChecker
from app.verification.job_checker import JobChecker
from app.verification.company_checker import CompanyChecker
from app.verification.url_checker import URLChecker, extract_domain
from app.verification.risk_engine import RiskEngine


class VerificationService:
    @classmethod
    async def verify_email(cls, user_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        company_name = payload.get("company_name", "")
        company_website = payload.get("company_website", "")
        sender_name = payload.get("sender_name", "")
        sender_email = payload.get("sender_email", "")
        subject = payload.get("subject", "")
        body = payload.get("body", "")

        company_domain = extract_domain(company_website) if company_website else None

        # Look up existing company in DB
        company = None
        if company_domain:
            company = fetch_one("SELECT * FROM companies WHERE domain = %s", (company_domain,))
        if not company and company_name:
            company = fetch_one("SELECT * FROM companies WHERE name LIKE %s", (f"%{company_name}%",))

        # Check Email Signals
        email_result = EmailChecker.check_email(
            sender_email=sender_email,
            subject=subject,
            body=body,
            company_name=company_name,
            company_domain=company_domain or (company["domain"] if company else None)
        )

        signals = RiskEngine.evaluate_email_signals(email_result)
        risk_score, risk_level, verification_status, recommended_actions = RiskEngine.calculate_risk_score(signals)

        summary = f"Email verification for '{sender_email}' regarding '{company_name}'. Risk Level: {risk_level} ({risk_score}/100)."

        # Save verification record in MySQL
        company_id = company["id"] if company else None
        verif_id = execute_query(
            """
            INSERT INTO verification_results
            (user_id, company_id, verification_type, risk_score, risk_level, verification_status, summary)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (user_id, company_id, "email", risk_score, risk_level, verification_status, summary)
        )

        # Save signals in MySQL
        saved_signals = []
        for s in signals:
            sig_id = execute_query(
                """
                INSERT INTO verification_signals
                (verification_id, signal_type, severity, title, description, evidence, score_impact)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (verif_id, s["signal_type"], s["severity"], s["title"], s["description"], s["evidence"], s["score_impact"])
            )
            s_copy = dict(s)
            s_copy["id"] = sig_id
            saved_signals.append(s_copy)

        return {
            "id": verif_id,
            "user_id": user_id,
            "company_id": company_id,
            "job_id": None,
            "verification_type": "email",
            "risk_score": risk_score,
            "risk_level": risk_level,
            "verification_status": verification_status,
            "summary": summary,
            "signals": saved_signals,
            "recommended_actions": recommended_actions
        }

    @classmethod
    async def verify_job(cls, user_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        job_url = payload.get("job_url", "")
        job_result = await JobChecker.check_job(job_url)

        signals = []
        if not job_result.get("valid"):
            signals.append(RiskEngine.create_signal(
                signal_type="SUSPICIOUS_URL",
                severity="HIGH",
                title="Invalid Job URL Format",
                description=job_result.get("error", "Invalid URL"),
                evidence=f"URL: {job_url}",
                score_impact=15
            ))
        else:
            url_an = job_result.get("url_analysis", {})
            if url_an.get("is_ip_address"):
                signals.append(RiskEngine.create_signal(
                    signal_type="SUSPICIOUS_URL",
                    severity="HIGH",
                    title="URL Uses IP Address Hostname",
                    description="Company portals use domain names, not IP addresses.",
                    evidence=f"Hostname: {url_an.get('hostname')}",
                    score_impact=20
                ))
            if not url_an.get("is_https"):
                signals.append(RiskEngine.create_signal(
                    signal_type="SUSPICIOUS_URL",
                    severity="MEDIUM",
                    title="Unencrypted HTTP Connection",
                    description="Job posting URL does not enforce secure HTTPS protocol.",
                    evidence=f"URL: {job_url}",
                    score_impact=10
                ))

            if job_result.get("detected_payments"):
                signals.append(RiskEngine.create_signal(
                    signal_type="PAYMENT_REQUEST",
                    severity="CRITICAL",
                    title="Job Text Mentions Payment Demands",
                    description="Job text references monetary payments required from applicants.",
                    evidence=f"Phrases: {', '.join(job_result['detected_payments'])}",
                    score_impact=30
                ))

        risk_score, risk_level, verification_status, recommended_actions = RiskEngine.calculate_risk_score(signals)
        summary = f"Job URL verification for '{job_url}'. Risk Level: {risk_level} ({risk_score}/100)."

        verif_id = execute_query(
            """
            INSERT INTO verification_results
            (user_id, verification_type, risk_score, risk_level, verification_status, summary)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (user_id, "job", risk_score, risk_level, verification_status, summary)
        )

        saved_signals = []
        for s in signals:
            sig_id = execute_query(
                """
                INSERT INTO verification_signals
                (verification_id, signal_type, severity, title, description, evidence, score_impact)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (verif_id, s["signal_type"], s["severity"], s["title"], s["description"], s["evidence"], s["score_impact"])
            )
            s_copy = dict(s)
            s_copy["id"] = sig_id
            saved_signals.append(s_copy)

        return {
            "id": verif_id,
            "user_id": user_id,
            "company_id": None,
            "job_id": None,
            "verification_type": "job",
            "risk_score": risk_score,
            "risk_level": risk_level,
            "verification_status": verification_status,
            "summary": summary,
            "signals": saved_signals,
            "recommended_actions": recommended_actions
        }

    @classmethod
    async def verify_company(cls, user_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        company_name = payload.get("company_name", "")
        website = payload.get("website", "")

        company_result = await CompanyChecker.check_company(company_name, website)
        signals = RiskEngine.evaluate_company_signals(company_result)

        domain = company_result.get("domain")
        company = None
        if domain:
            company = fetch_one("SELECT * FROM companies WHERE domain = %s", (domain,))

        risk_score, risk_level, verification_status, recommended_actions = RiskEngine.calculate_risk_score(signals)
        summary = f"Company verification for '{company_name}'. Reachable: {company_result.get('reachable')}. Risk Level: {risk_level} ({risk_score}/100)."

        company_id = company["id"] if company else None
        verif_id = execute_query(
            """
            INSERT INTO verification_results
            (user_id, company_id, verification_type, risk_score, risk_level, verification_status, summary)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (user_id, company_id, "company", risk_score, risk_level, verification_status, summary)
        )

        saved_signals = []
        for s in signals:
            sig_id = execute_query(
                """
                INSERT INTO verification_signals
                (verification_id, signal_type, severity, title, description, evidence, score_impact)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (verif_id, s["signal_type"], s["severity"], s["title"], s["description"], s["evidence"], s["score_impact"])
            )
            s_copy = dict(s)
            s_copy["id"] = sig_id
            saved_signals.append(s_copy)

        return {
            "id": verif_id,
            "user_id": user_id,
            "company_id": company_id,
            "job_id": None,
            "verification_type": "company",
            "risk_score": risk_score,
            "risk_level": risk_level,
            "verification_status": verification_status,
            "summary": summary,
            "signals": saved_signals,
            "recommended_actions": recommended_actions
        }

    @classmethod
    def get_history(cls, user_id: int) -> List[Dict[str, Any]]:
        verifs = fetch_all("SELECT * FROM verification_results WHERE user_id = %s ORDER BY id DESC", (user_id,))
        for v in verifs:
            signals = fetch_all("SELECT * FROM verification_signals WHERE verification_id = %s", (v["id"],))
            v["signals"] = signals
        return verifs

    @classmethod
    def get_details(cls, user_id: int, verification_id: int) -> Dict[str, Any]:
        verif = fetch_one("SELECT * FROM verification_results WHERE id = %s AND user_id = %s", (verification_id, user_id))
        if not verif:
            return None
        signals = fetch_all("SELECT * FROM verification_signals WHERE verification_id = %s", (verification_id,))
        _, _, _, actions = RiskEngine.calculate_risk_score(signals)
        verif["signals"] = signals
        verif["recommended_actions"] = actions
        return verif
