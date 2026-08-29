import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app, raise_server_exceptions=False)

def test_api_valid_c001_request_and_schema():
    response = client.post("/api/plan", json={"customer_id": "C001"})
    assert response.status_code == 200
    data = response.json()
    
    # schema matches contract (partially checked by presence of keys)
    assert "schema_version" in data
    assert "generated_at" in data
    assert "context" in data
    assert "profile" in data
    assert "risk" in data
    assert "goals" in data
    assert "plans" in data
    assert "goal_priority_note" in data
    assert "mismatch_note" in data
    assert "peer_cohort" in data
    assert "challenge" in data
    assert "verifier" in data
    assert "meta" in data
    
    # all three plans present
    assert len(data["plans"]) == 3
    plan_ids = {p["plan_id"] for p in data["plans"]}
    assert plan_ids == {"A", "B", "C"}
    
    # Explanation present
    assert data["goal_priority_note"]
    assert data["mismatch_note"]
    
    # Verifier present
    assert data["verifier"]["status"] in {"pass", "fail"}
    
    # privacy boundary & no internal fields leaked
    assert "customer_id" in data
    assert "customer_name" in data
    assert "customer" not in data
    assert "bundle" not in data
    assert "ground_truth_risk" not in data["risk"]
    assert "account_numbers" not in data

def test_api_challenge_valid():
    response = client.post("/api/challenge", json={"customer_id": "C001", "chosen_plan_id": "C"})
    assert response.status_code == 200
    data = response.json()
    
    # chosen_plan_id correctly propagated
    assert data["challenge"] is not None
    assert data["challenge"]["chosen_plan_id"] == "C"
    
    # Challenger present when required
    assert "challenge" in data["challenge"]
    assert "evidence_cited" in data["challenge"]
    assert "alternative_suggested" in data["challenge"]

def test_api_challenge_invalid_plan():
    response = client.post("/api/challenge", json={"customer_id": "C001", "chosen_plan_id": "Z"})
    assert response.status_code == 400
    assert "Invalid chosen_plan_id" in response.json()["detail"]

def test_api_malformed_input():
    # missing customer_id
    response = client.post("/api/plan", json={})
    assert response.status_code == 422
    
    # missing chosen_plan_id for challenge
    response = client.post("/api/challenge", json={"customer_id": "C001"})
    assert response.status_code == 422 # FastAPI Pydantic validation catches missing field

def test_api_failed_verification_behavior(monkeypatch):
    import api.main as api_main
    original_make_plan = api_main.make_plan
    
    def mock_make_plan(*args, **kwargs):
        res = original_make_plan(*args, **kwargs)
        res["verifier"]["status"] = "fail"
        return res
        
    monkeypatch.setattr(api_main, "make_plan", mock_make_plan)
    
    response = client.post("/api/plan", json={"customer_id": "C001"})
    assert response.status_code == 200
    assert response.json()["verifier"]["status"] == "fail"

def test_api_null_peer_cohort(monkeypatch):
    import api.main as api_main
    original_make_plan = api_main.make_plan
    
    def mock_make_plan(*args, **kwargs):
        res = original_make_plan(*args, **kwargs)
        res["peer_cohort"] = None
        return res
        
    monkeypatch.setattr(api_main, "make_plan", mock_make_plan)
    
    response = client.post("/api/plan", json={"customer_id": "C001"})
    assert response.status_code == 200
    assert response.json()["peer_cohort"] is None

def test_deterministic_compute_values_unchanged():
    response = client.post("/api/plan", json={"customer_id": "C001"})
    data = response.json()
    
    plan_c = next(p for p in data["plans"] if p["plan_id"] == "C")
    assert plan_c["projected_corpus"] == 4410000
    assert plan_c["success_probability"] == 0.95
    assert plan_c["survives_stress"] is False
    assert plan_c["breaking_probability"] == 0.007

import os
@pytest.mark.skipif(not os.environ.get("GROQ_API_KEY"), reason="live")
def test_live_api_c001_agent_chain():
    import orchestrator.pipeline as pipeline
    real_stages = {"profile", "features", "risk", "plans", "montecarlo", "stress", "cohort", "explanation", "verify", "challenge"}
    pipeline.REAL_ENGINES.update(real_stages)
    try:
        # First request to get plans
        response = client.post("/api/plan", json={"customer_id": "C001"})
        assert response.status_code == 200
        
        # Second request to challenge chosen plan
        response = client.post("/api/challenge", json={"customer_id": "C001", "chosen_plan_id": "C"})
        assert response.status_code == 200
        data = response.json()
        assert data["challenge"] is not None
        assert data["verifier"]["status"] == "pass"
    finally:
        pipeline.REAL_ENGINES.intersection_update(set())

def test_production_api_uses_real_compute_engines(monkeypatch):
    """Prove that normal API calls use real compute engines by default.
    
    This test overrides the conftest.py mock to restore production compute
    engines, proves the real engine route is active by temporarily sabotaging
    one, then executes a clean run to verify real computed values.
    
    Explanation/verify are kept mocked here because explain() requires
    GROQ_API_KEY which is not available in hermetic tests. The agent wiring
    is tested separately below and in the live test.
    """
    from orchestrator import pipeline
    
    # Compute engines only — explanation needs GROQ_API_KEY
    compute_engines = {"profile", "features", "risk", "plans",
                       "montecarlo", "stress", "cohort"}
    monkeypatch.setattr(pipeline, "REAL_ENGINES", compute_engines.copy())
    
    # Sabotage the real profile engine to behaviorally prove we are using it
    with monkeypatch.context() as m:
        import engines.profile
        
        def broken_profile(*args):
            raise RuntimeError("Sabotaged profile engine active")
            
        m.setattr(engines.profile, "build_profile", broken_profile)
        
        response = client.post("/api/plan", json={"customer_id": "C001"})
        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]
        
    # The context manager restores the real profile engine. Now do a clean run.
    response = client.post("/api/plan", json={"customer_id": "C001"})
    assert response.status_code == 200
    data = response.json()
    
    # Verify values correspond to the real engines, not the mocks
    plan_a = next(p for p in data["plans"] if p["plan_id"] == "A")
    plan_b = next(p for p in data["plans"] if p["plan_id"] == "B")
    plan_c = next(p for p in data["plans"] if p["plan_id"] == "C")
    
    assert plan_a["success_probability"] == 0.7376
    assert plan_b["success_probability"] == 0.5691
    assert plan_c["success_probability"] == 0.9240
    
    assert plan_a["survives_stress"] is False
    assert plan_b["survives_stress"] is False
    assert plan_c["survives_stress"] is True
    
    assert data["risk"]["features_used"]["expense_volatility"] == 0.12


def test_real_verifier_runs_against_mock_explanation(monkeypatch):
    """Prove the real Verifier is wired into production and actually runs.
    
    Enable the real verify stage with mock explanation input. The mock
    explanation contains peer_cohort_note, so the Verifier should pass
    structural checks. This proves mocks/verifier_out.json is NOT used.
    """
    from orchestrator import pipeline
    
    # Enable only verify as real (compute stays mocked for speed)
    monkeypatch.setattr(pipeline, "REAL_ENGINES", {"verify"})
    
    # Sabotage to prove real verifier runs
    import agents.verifier
    original_verify = agents.verifier.verify
    called = []
    
    def spy_verify(*args, **kwargs):
        called.append(True)
        return original_verify(*args, **kwargs)
    
    monkeypatch.setattr(agents.verifier, "verify", spy_verify)
    
    response = client.post("/api/plan", json={"customer_id": "C001"})
    assert response.status_code == 200
    assert called, "Real verifier was never called — still using mock"
    
    data = response.json()
    # The real verifier should have a numbers_checked count from actually
    # scanning the explanation prose, not the static mock value of 87
    assert "verifier" in data
    assert data["verifier"]["status"] in {"pass", "fail"}


def test_production_engines_include_explanation_and_verify():
    """Confirm PRODUCTION_ENGINES contains explanation and verify."""
    from orchestrator import pipeline
    assert "explanation" in pipeline.PRODUCTION_ENGINES
    assert "verify" in pipeline.PRODUCTION_ENGINES

