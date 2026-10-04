from typing import Any, Dict, List, Optional
from fastapi import status
from pymysql.connections import Connection
from app.database import fetch_one, fetch_all, execute
from app.schemas.verification import (
    EmailVerificationRequest,
    JobVerificationRequest,
    CompanyVerificationRequest,
)
from app.verification.email_analyzer import EmailAnalyzer
from app.verification.company_analyzer import CompanyAnalyzer
from app.verification.job_analyzer import JobAnalyzer
from app.verification.signal_detector import SignalDetector
from app.verification.risk_engine import RiskEngine
from app.utils.validators import extract_domain
from app.core.exceptions import CustomAPIException


class VerificationService:
    """
    Every verification follows the same 4 steps:
      1. Analyzers collect raw facts (domain, keywords, website reachability ...)
      2. SignalDetector turns those facts into signals (each has a severity + score impact)
      3. RiskEngine adds up the score impacts -> risk score, level, status, advice
      4. We save the result + its signals in MySQL and return them
    """

    # ---------- helpers ----------

    @staticmethod
    def _save_verification(
        db: Connection,
        user_id: int,
        verification_type: str,
        company_id: Optional[int],
        signals: List[Dict[str, Any]],
        summary_builder,
    ) -> Dict[str, Any]:
        """Run the risk engine, then store the result and its signals in one transaction."""
        risk_score, risk_level, verification_status, recommended_actions = RiskEngine.calculate_risk_score(signals)
        summary = summary_builder(risk_level, risk_score, verification_status)

        verification_id = execute(
            db,
            """INSERT INTO verification_results
                   (user_id, company_id, verification_type, risk_score, risk_level, verification_status, summary)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (user_id, company_id, verification_type, risk_score, risk_level, verification_status, summary),
        )
        for sig in signals:
            execute(
                db,
                """INSERT INTO verification_signals
                       (verification_id, signal_type, severity, title, description, evidence, score_impact)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (
                    verification_id,
                    sig["signal_type"],
                    sig["severity"],
                    sig["title"],
                    sig["description"],
                    sig["evidence"],
                    sig["score_impact"],
                ),
            )
        db.commit()  # result + all signals saved together, or not at all

        result = fetch_one(db, "SELECT * FROM verification_results WHERE id = %s", (verification_id,))
        result["signals"] = fetch_all(
            db, "SELECT * FROM verification_signals WHERE verification_id = %s", (verification_id,)
        )
        result["recommended_actions"] = recommended_actions
        return result

    # ---------- verify endpoints ----------

    @classmethod
    async def verify_email(cls, db: Connection, user_id: int, req: EmailVerificationRequest) -> Dict[str, Any]:
        company_domain = extract_domain(req.company_website) if req.company_website else None

        # Is this company already in our database? Match by domain first, then by name.
        company = None
        if company_domain:
            company = fetch_one(db, "SELECT * FROM companies WHERE domain = %s", (company_domain,))
        if not company:
            company = fetch_one(db, "SELECT * FROM companies WHERE name LIKE %s", (f"%{req.company_name}%",))

        email_analysis = EmailAnalyzer.analyze_email(
            sender_email=req.sender_email,
            subject=req.subject,
            body=req.body,
            company_name=req.company_name,
            company_domain=company_domain or (company["domain"] if company else None),
        )
        signals = SignalDetector.detect_email_signals(email_analysis)

        return cls._save_verification(
            db, user_id, "email",
            company["id"] if company else None,
            signals,
            lambda level, score, _status: (
                f"Email verification for {req.sender_email} regarding '{req.company_name}'. "
                f"Risk Level: {level} (Score: {score}/100). {len(signals)} risk signals detected."
            ),
        )

    @classmethod
    async def verify_job(cls, db: Connection, user_id: int, req: JobVerificationRequest) -> Dict[str, Any]:
        job_analysis = await JobAnalyzer.analyze_job_url(req.job_url)

        signals = []
        if not job_analysis.get("valid"):
            signals.append(SignalDetector.create_signal(
                signal_type="SUSPICIOUS_URL",
                severity="HIGH",
                title="Invalid or Malformed Job URL",
                description=job_analysis.get("error", "URL format is invalid"),
                evidence=f"Input URL: {req.job_url}",
                score_impact=15,
            ))
        else:
            url_info = job_analysis.get("url_analysis", {})
            if url_info.get("is_ip_address"):
                signals.append(SignalDetector.create_signal(
                    signal_type="SUSPICIOUS_URL",
                    severity="HIGH",
                    title="URL Uses Raw IP Address Hostname",
                    description="Legitimate company job portals use registered domain names, not raw IP addresses.",
                    evidence=f"Hostname: {url_info.get('hostname')}",
                    score_impact=20,
                ))
            if not url_info.get("is_https"):
                signals.append(SignalDetector.create_signal(
                    signal_type="SUSPICIOUS_URL",
                    severity="MEDIUM",
                    title="Unencrypted HTTP Connection",
                    description="Job posting URL does not enforce secure HTTPS protocol.",
                    evidence=f"URL: {req.job_url}",
                    score_impact=10,
                ))
            if job_analysis.get("detected_payments"):
                signals.append(SignalDetector.create_signal(
                    signal_type="PAYMENT_REQUEST",
                    severity="CRITICAL",
                    title="Job Description Contains Payment/Fee Mentions",
                    description="Job text references monetary payments or fees required from applicants.",
                    evidence=f"Phrases: {', '.join(job_analysis['detected_payments'])}",
                    score_impact=30,
                ))

        return cls._save_verification(
            db, user_id, "job", None, signals,
            lambda level, score, status_: (
                f"Job URL verification for '{req.job_url}'. Status: {status_}, Risk: {level} ({score}/100)."
            ),
        )

    @classmethod
    async def verify_company(cls, db: Connection, user_id: int, req: CompanyVerificationRequest) -> Dict[str, Any]:
        company_analysis = await CompanyAnalyzer.analyze_company(req.company_name, req.website)
        signals = SignalDetector.detect_company_signals(company_analysis)

        # Link the result to a company row if we already know this domain
        company = None
        domain = company_analysis.get("domain")
        if domain:
            company = fetch_one(db, "SELECT * FROM companies WHERE domain = %s", (domain,))

        return cls._save_verification(
            db, user_id, "company",
            company["id"] if company else None,
            signals,
            lambda level, score, _status: (
                f"Company verification for '{req.company_name}' ({req.website}). "
                f"Website Reachable: {company_analysis.get('reachable')}. Risk: {level} ({score}/100)."
            ),
        )

    # ---------- read endpoints ----------

    @classmethod
    def get_user_history(cls, db: Connection, user_id: int) -> List[Dict[str, Any]]:
        results = fetch_all(
            db, "SELECT * FROM verification_results WHERE user_id = %s ORDER BY id DESC", (user_id,)
        )
        if not results:
            return []

        # One query for ALL signals of these results (instead of one query per result)
        ids = [r["id"] for r in results]
        placeholders = ", ".join(["%s"] * len(ids))
        signals = fetch_all(
            db, f"SELECT * FROM verification_signals WHERE verification_id IN ({placeholders})", ids
        )

        signals_by_result: Dict[int, List[dict]] = {r_id: [] for r_id in ids}
        for sig in signals:
            signals_by_result[sig["verification_id"]].append(sig)
        for r in results:
            r["signals"] = signals_by_result[r["id"]]
        return results

    @classmethod
    def get_verification_details(cls, db: Connection, user_id: int, verification_id: int) -> Dict[str, Any]:
        result = fetch_one(
            db,
            "SELECT * FROM verification_results WHERE id = %s AND user_id = %s",
            (verification_id, user_id),
        )
        if not result:
            raise CustomAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                code="VERIFICATION_NOT_FOUND",
                message=f"Verification result with ID {verification_id} was not found.",
            )

        signals = fetch_all(
            db, "SELECT * FROM verification_signals WHERE verification_id = %s", (verification_id,)
        )
        # Recommended actions are not stored, so we recompute them from the saved signals
        _, _, _, recommended_actions = RiskEngine.calculate_risk_score(signals)

        result["signals"] = signals
        result["recommended_actions"] = recommended_actions
        return result
