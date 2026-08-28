import os
import json
import pytest
from agents.explanation import build_explanation_payload, explain
from orchestrator import pipeline
import groq

def test_explanation_payload_schema_and_privacy():
    """Verify C001 produces a valid payload with no PII or ground_truth_risk."""
    real_stages = {"profile", "features", "risk", "plans", "montecarlo", "stress", "cohort"}
    original_real = set(pipeline.REAL_ENGINES)
    pipeline.REAL_ENGINES.update(real_stages)
    try:
        s = pipeline.run_engines("C001")
        bundle = s["bundle"]
        
        payload = build_explanation_payload(bundle)
        
        # 1. Correct payload schema
        expected_keys = {"context", "profile", "risk", "goals", "plans", "comparisons", "n_simulations", "peer_cohort"}
        assert set(payload.keys()) == expected_keys
        
        # 2. Privacy verification
        payload_json = json.dumps(payload)
        assert "Jane" not in payload_json
        assert "C001" not in payload_json
        assert "G00" not in payload_json  # Synthetic customer IDs start with G00
        assert "ground_truth_risk" not in payload_json
        
        # 3. Numeric pass-through verification
        assert payload["profile"]["monthly_surplus"] == bundle["profile"]["monthly_surplus"]
        assert payload["risk"]["stated"] == bundle["risk"]["stated"]
        assert payload["risk"]["confidence"] == bundle["risk"]["confidence"]
        assert payload["n_simulations"] == 10000
        assert payload["peer_cohort"]["customer_savings_rate"] == s["cohort"]["customer_savings_rate"]
        
        # 4. Plan pass-through
        assert len(payload["plans"]) == 3
        assert payload["plans"][0]["monthly_investment"] == bundle["plans"][0]["monthly_investment"]
        
    finally:
        pipeline.REAL_ENGINES.clear()
        pipeline.REAL_ENGINES.update(original_real)

def test_null_cohort_handling():
    """Verify payload builder handles missing cohort data safely."""
    bundle = {
        "context": {}, "profile": {}, "risk": {}, "goals": [], "plans": [],
        "comparisons": {}, "n_simulations": 10000, "peer_cohort": None
    }
    payload = build_explanation_payload(bundle)
    assert payload["peer_cohort"] is None
    assert payload["n_simulations"] == 10000

def test_determinism():
    """Verify repeated calls yield identical payloads."""
    bundle = {
        "context": {"age": 28},
        "profile": {"monthly_surplus": 45000},
        "risk": {"stated": "aggressive"},
        "peer_cohort": None
    }
    p1 = build_explanation_payload(bundle)
    p2 = build_explanation_payload(bundle)
    assert p1 == p2

def test_missing_api_key_raises_error(monkeypatch):
    """Verify that explain() raises a clear error when GROQ_API_KEY is missing."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(ValueError, match="GROQ_API_KEY environment variable is not set"):
        explain({})

class MockChoices:
    def __init__(self, content):
        self.message = type("Msg", (), {"content": content})
class MockResponse:
    def __init__(self, content):
        self.choices = [MockChoices(content)]

def mock_groq_client(content, assert_model=None, assert_schema=False):
    class MockClient:
        class Chat:
            class Completions:
                def create(self, **kwargs):
                    if assert_model:
                        assert kwargs["model"] == assert_model
                    if assert_schema:
                        fmt = kwargs["response_format"]
                        assert fmt["type"] == "json_schema"
                        assert fmt["json_schema"]["strict"] is True
                        assert "plans_text" in fmt["json_schema"]["schema"]["properties"]
                    return MockResponse(content)
            completions = Completions()
        chat = Chat()
    return MockClient()

def test_model_is_configurable_and_uses_schema(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "fake")
    monkeypatch.setenv("GROQ_MODEL", "custom-model-8b")
    bundle = {"peer_cohort": None, "profile": {"a": 100}}
    valid_out = json.dumps({
        "plans_text": [{"plan_id": "A", "headline": "h", "body": "b", "pros": ["p"], "cons": ["c"]}],
        "goal_priority_note": "note",
        "mismatch_note": "note",
        "numbers_used": [100.0]
    })
    
    monkeypatch.setattr(groq, "Groq", lambda api_key: mock_groq_client(valid_out, assert_model="custom-model-8b", assert_schema=True))
    res = explain(bundle)
    assert res["goal_priority_note"] == "note"

def test_explain_validates_schema(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "fake")
    bundle = {"peer_cohort": None, "profile": {"a": 100}}
    
    # Invalid structure (missing body)
    invalid_struct = json.dumps({
        "plans_text": [{"plan_id": "A", "headline": "h", "pros": [], "cons": []}],
        "goal_priority_note": "note",
        "mismatch_note": "note",
        "numbers_used": [100.0]
    })
    monkeypatch.setattr(groq, "Groq", lambda api_key: mock_groq_client(invalid_struct))
    with pytest.raises(ValueError, match="Missing required field in plan_text"):
        explain(bundle)
        
    invalid_struct2 = json.dumps({
        "plans_text": [{"plan_id": "A", "headline": "h", "body": "b", "pros": ["p"], "cons": ["c"]}],
        "goal_priority_note": "note",
        "numbers_used": [100.0]
    })
    monkeypatch.setattr(groq, "Groq", lambda api_key: mock_groq_client(invalid_struct2))
    with pytest.raises(ValueError, match="Missing or invalid 'mismatch_note'"):
        explain(bundle)

def test_explain_rejects_unsupported_numbers_used(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "fake")
    bundle = {"peer_cohort": None, "profile": {"a": 100}}
    
    out = json.dumps({
        "plans_text": [{"plan_id": "A", "headline": "h", "body": "b", "pros": [], "cons": []}],
        "goal_priority_note": "note",
        "mismatch_note": "note",
        "numbers_used": [100.0, 200.0]
    })
    
    monkeypatch.setattr(groq, "Groq", lambda api_key: mock_groq_client(out))
    with pytest.raises(ValueError, match="Unsupported numeric claim"):
        explain(bundle)

def test_explain_rejects_unsupported_prose_number(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "fake")
    bundle = {"peer_cohort": None, "profile": {"a": 100}}
    
    out = json.dumps({
        "plans_text": [{"plan_id": "A", "headline": "h", "body": "It costs 250 dollars", "pros": [], "cons": []}],
        "goal_priority_note": "note",
        "mismatch_note": "note",
        "numbers_used": [100.0]
    })
    
    monkeypatch.setattr(groq, "Groq", lambda api_key: mock_groq_client(out))
    with pytest.raises(ValueError, match="Unsupported numeric claim in prose: 250"):
        explain(bundle)

def test_valid_formatting_variant_is_accepted(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "fake")
    # payload contains 0.7376
    bundle = {"peer_cohort": None, "profile": {"rate": 0.7376, "cost": 2500000}}
    
    out = json.dumps({
        "plans_text": [{"plan_id": "A", "headline": "Rate 73.76%", "body": "Cost 2,500,000", "pros": [], "cons": []}],
        "goal_priority_note": "note",
        "mismatch_note": "note",
        "numbers_used": [0.7376, 2500000]
    })
    
    monkeypatch.setattr(groq, "Groq", lambda api_key: mock_groq_client(out))
    res = explain(bundle)
    assert res["numbers_used"] == [0.7376, 2500000]

def test_explain_rejects_privacy_leaks(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "fake")
    bundle = {"peer_cohort": None, "profile": {"a": 100}}
    
    out = json.dumps({
        "plans_text": [{"plan_id": "A", "headline": "h", "body": "C001 is the user", "pros": [], "cons": []}],
        "goal_priority_note": "note",
        "mismatch_note": "note",
        "numbers_used": [100.0]
    })
    
    monkeypatch.setattr(groq, "Groq", lambda api_key: mock_groq_client(out))
    with pytest.raises(ValueError, match="Privacy violation: 'c001' found"):
        explain(bundle)

@pytest.mark.skipif(not os.environ.get("GROQ_API_KEY"), reason="Requires GROQ_API_KEY")
def test_explanation_live_groq():
    """Live integration test with Groq API for C001."""
    real_stages = {"profile", "features", "risk", "plans", "montecarlo", "stress", "cohort"}
    original_real = set(pipeline.REAL_ENGINES)
    pipeline.REAL_ENGINES.update(real_stages)
    try:
        s = pipeline.run_engines("C001")
        bundle = s["bundle"]
        result = explain(bundle)
        
        # Verify schema
        assert isinstance(result["plans_text"], list)
        assert isinstance(result["goal_priority_note"], str)
        assert isinstance(result["numbers_used"], list)
        
        print("\n=== LIVE EXPLANATION RESULT ===")
        print(json.dumps(result, indent=2))
        
    finally:
        pipeline.REAL_ENGINES.clear()
        pipeline.REAL_ENGINES.update(original_real)
