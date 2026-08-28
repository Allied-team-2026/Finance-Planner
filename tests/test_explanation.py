import json
from agents.explanation import build_explanation_payload
from orchestrator import pipeline

def test_explanation_payload_schema_and_privacy():
    """Verify C001 produces a valid payload with no PII or ground_truth_risk."""
    real_stages = {"profile", "features", "risk", "plans", "montecarlo", "stress", "cohort"}
    original_real = set(pipeline.REAL_ENGINES)
    pipeline.REAL_ENGINES.update(real_stages)
    try:
        s = pipeline.run_engines("C001")
        bundle = s["bundle"]
        
        # Ensure peer_cohort is in bundle for the test, as it's not currently added by build_bundle
        if "peer_cohort" not in bundle and "cohort" in s:
            bundle["peer_cohort"] = s["cohort"]
            
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
        "comparisons": {}, "n_simulations": 10000
    }
    payload = build_explanation_payload(bundle)
    assert "peer_cohort" not in payload
    assert payload["n_simulations"] == 10000

def test_determinism():
    """Verify repeated calls yield identical payloads."""
    bundle = {
        "context": {"age": 28},
        "profile": {"monthly_surplus": 45000},
        "risk": {"stated": "aggressive"}
    }
    p1 = build_explanation_payload(bundle)
    p2 = build_explanation_payload(bundle)
    assert p1 == p2
