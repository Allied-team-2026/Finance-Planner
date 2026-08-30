import json
import pytest
from orchestrator import pipeline
from agents.challenger import build_challenger_payload

@pytest.fixture
def base_bundle():
    return {
        "customer_id": "C001",
        "customer_name": "Rahul Mehta",
        "transactions": [{"date": "2026-07-05", "amount": 25000}],
        "investment_events": [{"date": "2024-03-12", "action": "sell"}],
        "profile": {"monthly_surplus": 45000},
        "risk": {"ground_truth_risk": "moderate", "stated": "aggressive"},
        "goals": [{"name": "house", "target_amount": 2500000}],
        "plans": [{"plan_id": "A", "monthly_investment": 35000}],
        "comparisons": {"cheapest_plan_id": "B"},
        "n_simulations": 10000,
        "peer_cohort": {"cohort_size": 20, "individual_peers": ["P1", "P2"]}
    }

@pytest.fixture
def base_explanation():
    return {"plans_text": [{"plan_id": "A", "body": "Invest 35000"}]}

@pytest.fixture
def base_verification():
    return {"status": "fail", "unverified_numbers": [36000]}

def test_schema_inclusion(base_bundle, base_explanation, base_verification):
    payload = build_challenger_payload(base_bundle, base_explanation, base_verification)
    assert "explanation" in payload
    assert payload["explanation"] == base_explanation
    assert "verification" in payload
    assert payload["verification"] == base_verification
    assert "profile" in payload
    assert "risk" in payload
    assert "plans" in payload

def test_privacy_and_leaks(base_bundle, base_explanation, base_verification):
    payload = build_challenger_payload(base_bundle, base_explanation, base_verification)
    payload_str = json.dumps(payload).lower()
    
    assert "c001" not in payload_str
    assert "rahul mehta" not in payload_str
    assert "transactions" not in payload
    assert "investment_events" not in payload
    assert "ground_truth_risk" not in payload_str
    assert "individual_peers" not in payload_str
    assert "p1" not in payload_str
    
def test_null_cohort(base_bundle, base_explanation, base_verification):
    base_bundle["peer_cohort"] = None
    payload = build_challenger_payload(base_bundle, base_explanation, base_verification)
    assert payload["peer_cohort"] is None
    
def test_engine_number_passthrough(base_bundle, base_explanation, base_verification):
    payload = build_challenger_payload(base_bundle, base_explanation, base_verification)
    assert payload["profile"]["monthly_surplus"] == 45000
    assert payload["plans"][0]["monthly_investment"] == 35000
    
def test_deterministic_output(base_bundle, base_explanation, base_verification):
    payload1 = build_challenger_payload(base_bundle, base_explanation, base_verification)
    payload2 = build_challenger_payload(base_bundle, base_explanation, base_verification)
    assert json.dumps(payload1) == json.dumps(payload2)

def test_c001_real_payload():
    real_stages = {"profile", "features", "risk", "plans", "montecarlo", "stress", "cohort"}
    original_real = set(pipeline.REAL_ENGINES)
    pipeline.REAL_ENGINES.update(real_stages)
    try:
        s = pipeline.run_engines("C001")
    finally:
        pipeline.REAL_ENGINES = original_real
        
    bundle = s["bundle"]
    expl = {"dummy": "explanation"}
    verif = {"status": "pass"}
    
    payload = build_challenger_payload(bundle, expl, verif)
    payload_str = json.dumps(payload).lower()
    
    assert "c001" not in payload_str
    assert "ground_truth_risk" not in payload_str
    assert "transactions" not in payload
    assert payload["explanation"] == expl
    assert payload["verification"] == verif
    assert payload["profile"]["monthly_surplus"] == 45000
    assert payload["peer_cohort"]["cohort_size"] == 20

import os
from unittest.mock import patch, MagicMock

@pytest.fixture
def base_groq_response():
    return {
        "chosen_plan_id": "C",
        "challenge": "Plan C invests 52000, which exceeds the 45000 surplus.",
        "evidence_cited": ["Surplus is 45000"],
        "alternative_suggested": "A",
        "numbers_used": [52000, 45000, 35000]
    }

def mock_groq_client(response_dict):
    mock = MagicMock()
    mock.chat.completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content=json.dumps(response_dict)))
    ]
    return mock

@patch("groq.Groq")
@patch.dict(os.environ, {"GROQ_API_KEY": "fake_key"})
def test_valid_challenge_passes(mock_groq, base_bundle, base_explanation, base_verification, base_groq_response):
    base_bundle["plans"].append({"plan_id": "C", "monthly_investment": 52000})
    mock_groq.return_value = mock_groq_client(base_groq_response)
    from agents.challenger import challenge
    result = challenge(base_bundle, base_explanation, base_verification, "C")
    assert result["chosen_plan_id"] == "C"
    assert "Plan C invests" in result["challenge"]

@patch("groq.Groq")
@patch.dict(os.environ, {"GROQ_API_KEY": "fake_key"})
def test_wrong_chosen_plan_id_fails(mock_groq, base_bundle, base_explanation, base_verification, base_groq_response):
    base_groq_response["chosen_plan_id"] = "A"
    mock_groq.return_value = mock_groq_client(base_groq_response)
    from agents.challenger import challenge
    with pytest.raises(ValueError, match="does not match input"):
        challenge(base_bundle, base_explanation, base_verification, "C")

@patch("groq.Groq")
@patch.dict(os.environ, {"GROQ_API_KEY": "fake_key"})
def test_fabricated_number_fails(mock_groq, base_bundle, base_explanation, base_verification, base_groq_response):
    base_bundle["plans"].append({"plan_id": "C", "monthly_investment": 52000})
    base_groq_response["challenge"] += " And 99999 fabricated."
    mock_groq.return_value = mock_groq_client(base_groq_response)
    from agents.challenger import challenge
    with pytest.raises(ValueError, match="not found in payload"):
        challenge(base_bundle, base_explanation, base_verification, "C")

@patch("groq.Groq")
@patch.dict(os.environ, {"GROQ_API_KEY": "fake_key"})
def test_privacy_leak_fails(mock_groq, base_bundle, base_explanation, base_verification, base_groq_response):
    base_bundle["plans"].append({"plan_id": "C", "monthly_investment": 52000})
    base_groq_response["challenge"] += " Customer C001."
    mock_groq.return_value = mock_groq_client(base_groq_response)
    from agents.challenger import challenge
    with pytest.raises(ValueError, match="Privacy violation"):
        challenge(base_bundle, base_explanation, base_verification, "C")

@patch("groq.Groq")
@patch.dict(os.environ, {"GROQ_API_KEY": "fake_key"})
def test_ground_truth_risk_leak_fails(mock_groq, base_bundle, base_explanation, base_verification, base_groq_response):
    base_bundle["plans"].append({"plan_id": "C", "monthly_investment": 52000})
    base_groq_response["challenge"] += " ground_truth_risk is moderate."
    mock_groq.return_value = mock_groq_client(base_groq_response)
    from agents.challenger import challenge
    with pytest.raises(ValueError, match="Privacy violation"):
        challenge(base_bundle, base_explanation, base_verification, "C")

@patch("groq.Groq")
@patch.dict(os.environ, {"GROQ_API_KEY": "fake_key"})
def test_missing_required_field(mock_groq, base_bundle, base_explanation, base_verification, base_groq_response):
    base_bundle["plans"].append({"plan_id": "C", "monthly_investment": 52000})
    del base_groq_response["challenge"]
    mock_groq.return_value = mock_groq_client(base_groq_response)
    from agents.challenger import challenge
    with pytest.raises(ValueError, match="Missing or invalid"):
        challenge(base_bundle, base_explanation, base_verification, "C")


@patch("groq.Groq")
@patch.dict(os.environ, {"GROQ_API_KEY": "fake_key"})
def test_percentile_label_is_not_a_peer_id(mock_groq, base_bundle, base_explanation,
                                           base_verification, base_groq_response):
    """p10 names a number the bundle hands over, not a person.

    This is the bug that made challenging plan A return nothing: the plan with the
    worst downside is the one worth challenging, the downside field is p10_corpus,
    and the old regex read "the p10 outcome" as an individual peer ID and refused
    the whole challenge.
    """
    base_bundle["plans"].append({"plan_id": "C", "monthly_investment": 52000,
                                 "p10_corpus": 1855503})
    base_groq_response["challenge"] += " The p10 outcome reaches only 1855503."
    base_groq_response["numbers_used"].append(1855503)
    mock_groq.return_value = mock_groq_client(base_groq_response)
    from agents.challenger import challenge
    result = challenge(base_bundle, base_explanation, base_verification, "C")
    assert "p10" in result["challenge"]


@patch("groq.Groq")
@patch.dict(os.environ, {"GROQ_API_KEY": "fake_key"})
def test_real_peer_id_still_fails(mock_groq, base_bundle, base_explanation,
                                  base_verification, base_groq_response):
    """Non-vacuity guard for the test above: P2 is a person and must be refused."""
    base_bundle["plans"].append({"plan_id": "C", "monthly_investment": 52000})
    base_groq_response["challenge"] += " Peer P2 saved more than you."
    mock_groq.return_value = mock_groq_client(base_groq_response)
    from agents.challenger import challenge
    with pytest.raises(ValueError, match="individual peer ID"):
        challenge(base_bundle, base_explanation, base_verification, "C")


@patch("groq.Groq")
@patch.dict(os.environ, {"GROQ_API_KEY": "fake_key"})
def test_previous_failure_is_handed_back_to_the_model(mock_groq, base_bundle,
                                                      base_explanation,
                                                      base_verification,
                                                      base_groq_response):
    """A retry that does not say what was wrong is just the same call again."""
    base_bundle["plans"].append({"plan_id": "C", "monthly_investment": 52000})
    client = mock_groq_client(base_groq_response)
    mock_groq.return_value = client
    from agents.challenger import challenge
    challenge(base_bundle, base_explanation, base_verification, "C",
              ["Unsupported numeric claim in prose: 1.35"])
    sent = client.chat.completions.create.call_args.kwargs["messages"][0]["content"]
    assert "1.35" in sent


def fallback_bundle():
    """C001's bundle from the engine mocks - no LLM and no trained model needed."""
    return pipeline.run_engines("C001")["bundle"]


@pytest.mark.parametrize("plan_id", ["A", "B", "C"])
def test_fallback_challenge_passes_verification(plan_id):
    """The fallback exists to be shown when the model's tries were all refused,
    so it has to satisfy the same checks the model's output does."""
    from agents.challenger import fallback_challenge
    from agents.verifier import verify_challenge
    bundle = fallback_bundle()
    result = verify_challenge(fallback_challenge(bundle, plan_id), bundle)
    assert result["status"] == "pass", result
    assert result["numbers_checked"] > 0


@pytest.mark.parametrize("plan_id", ["A", "B", "C"])
def test_fallback_challenge_answers_about_the_right_plan(plan_id):
    from agents.challenger import fallback_challenge
    result = fallback_challenge(fallback_bundle(), plan_id)
    assert result["chosen_plan_id"] == plan_id
    assert result["alternative_suggested"] != plan_id

