from app.verification.posting_analyzer import PostingAnalyzer
from app.verification.risk_engine import RiskEngine


def _types(signals):
    return {s["signal_type"] for s in signals}


def _complete(**kw):
    """A posting that has every structural field, so only text rules can fire."""
    base = {"title": "Analyst", "description": "Build dashboards.", "has_company_profile": 1,
            "has_company_logo": 1, "has_questions": 1}
    base.update(kw)
    return base


def test_clean_complete_posting_has_no_signals():
    assert PostingAnalyzer.analyze(_complete()) == []


def test_fee_keyword_triggers_registration_fee_signal():
    signals = PostingAnalyzer.analyze(_complete(description="Pay a registration fee to start."))
    assert "REGISTRATION_FEE" in _types(signals)
    score, level, _, _ = RiskEngine.calculate_risk_score(signals)
    assert score == 25 and level == "MODERATE"


def test_text_rules_reuse_email_keyword_lists():
    signals = PostingAnalyzer.analyze(_complete(
        description="Selected without interview. Offer expires in 24 hours. Message t.me/jobs"))
    assert {"NO_INTERVIEW_SELECTION", "URGENT_LANGUAGE", "SUSPICIOUS_URL"} <= _types(signals)


def test_requirements_and_benefits_are_also_searched():
    signals = PostingAnalyzer.analyze(_complete(benefits="Free laptop after you pay the processing fee"))
    assert "PAYMENT_REQUEST" in _types(signals)


def test_structure_signals_for_missing_fields():
    signals = PostingAnalyzer.analyze({"title": "x", "description": "y"})
    assert _types(signals) == {"NO_COMPANY_PROFILE", "NO_COMPANY_LOGO", "NO_SCREENING_QUESTIONS"}
    assert RiskEngine.calculate_risk_score(signals)[0] == 20


def test_known_false_positive_crypto_in_a_legitimate_job():
    # Documented weakness: the keyword "crypto" also appears in honest blockchain jobs.
    signals = PostingAnalyzer.analyze(_complete(description="Build a crypto exchange backend."))
    assert "PAYMENT_REQUEST" in _types(signals)


def test_missing_text_fields_are_ignored_not_read_as_the_word_nan():
    # Regression: NaN from pandas must not be turned into text.
    nan = float("nan")
    posting = {"title": "Analyst", "description": nan, "requirements": None, "benefits": nan,
               "has_company_profile": 1, "has_company_logo": 1, "has_questions": 1}
    assert PostingAnalyzer.build_text(posting) == "analyst"
    assert PostingAnalyzer.analyze(posting) == []
