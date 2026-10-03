from app.verification.email_analyzer import EmailAnalyzer
from app.verification.url_analyzer import URLAnalyzer
from app.verification.signal_detector import SignalDetector
from app.verification.risk_engine import RiskEngine

def test_email_analyzer_personal_email():
    res = EmailAnalyzer.analyze_email(
        sender_email="recruiter@gmail.com",
        subject="Job Offer",
        body="Join our company",
        company_name="Tech Corp",
        company_domain="techcorp.com"
    )
    assert res["is_free_email"] is True


def test_email_analyzer_domain_mismatch():
    res = EmailAnalyzer.analyze_email(
        sender_email="hr@fakecompany.com",
        subject="Offer",
        body="Work for Tech Corp",
        company_name="Tech Corp",
        company_domain="techcorp.com"
    )
    assert res["domain_mismatch"] is True


def test_signal_detector_payment_fee():
    analysis = {
        "sender_email": "hr@fakecompany.com",
        "is_free_email": True,
        "domain_mismatch": True,
        "detected_payments": ["registration fee"],
        "detected_urgency": [],
        "detected_no_interview": [],
        "detected_links": []
    }
    signals = SignalDetector.detect_email_signals(analysis)
    signal_types = [s["signal_type"] for s in signals]
    assert "REGISTRATION_FEE" in signal_types
    assert "PERSONAL_EMAIL" in signal_types
    assert "DOMAIN_MISMATCH" in signal_types


def test_risk_engine_calculation():
    signals = [
        {"signal_type": "REGISTRATION_FEE", "severity": "CRITICAL", "score_impact": 25},
        {"signal_type": "DOMAIN_MISMATCH", "severity": "HIGH", "score_impact": 15},
        {"signal_type": "PERSONAL_EMAIL", "severity": "MEDIUM", "score_impact": 10}
    ]
    score, level, status, actions = RiskEngine.calculate_risk_score(signals)
    assert score == 50
    assert level == "HIGH"
    assert status == "VERIFIED_SIGNALS_FOUND"
    assert len(actions) > 0


def test_url_analyzer_ip_address():
    res = URLAnalyzer.analyze_url("http://192.168.1.1/job/apply")
    assert res["is_ip_address"] is True
    assert res["is_https"] is False


def test_email_verification_api(client, auth_headers):
    payload = {
        "company_name": "TechCorp",
        "company_website": "https://techcorp.com",
        "sender_name": "Scammer HR",
        "sender_email": "hr@gmail.com",
        "subject": "Selection Notice",
        "body": "Congratulations! Pay registration fee of $50 to reserve laptop."
    }
    res = client.post("/api/v1/verification/email", json=payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["risk_score"] > 30
    assert data["risk_level"] in ["HIGH", "VERY_HIGH", "MODERATE"]
    assert len(data["signals"]) >= 2
