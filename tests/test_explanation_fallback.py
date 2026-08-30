import sys
from pathlib import Path
import json
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from orchestrator.pipeline import run_engines, REAL_ENGINES
from agents.explanation import fallback_explain
from agents.verifier import verify

def test_fallback_passes_real_verifier():
    """Proves the actual fallback text passes the actual Verifier using real engine outputs."""
    
    # 1. Build a real C001 bundle using current real engines
    original_real_engines = set(REAL_ENGINES)
    REAL_ENGINES.update({"profile", "features", "risk", "plans", "montecarlo", "stress", "cohort"})
    
    try:
        s = run_engines("C001")
        bundle = s["bundle"]
        
        # 2. Call fallback_explain(bundle)
        fallback_expl = fallback_explain(bundle)
        
        # 3. Pass fallback directly into the REAL verify
        verification = verify(fallback_expl, bundle)
        
        # 4. Assert status == "pass"
        assert verification["status"] == "pass", f"Verification failed: {verification}"
        
        # 5. Assert unverified_numbers == []
        assert verification["unverified_numbers"] == []
        
        # 6. Assert no privacy violations
        fallback_str = json.dumps(fallback_expl).lower()
        forbidden = ["c001", "rahul", "mehta", "ground_truth_risk", "raw transaction", "investment_event"]
        for term in forbidden:
            assert term not in fallback_str, f"Privacy violation: found '{term}' in fallback output."
            
    finally:
        REAL_ENGINES.clear()
        REAL_ENGINES.update(original_real_engines)

from unittest.mock import patch, MagicMock
from orchestrator.pipeline import run_stages
import groq

@patch("orchestrator.pipeline.run_engines")
@patch("orchestrator.pipeline.run")
def test_groq_badrequest_retry_logic(mock_run, mock_run_engines):
    """
    Tests various combinations of API/Groq errors and retry scenarios.
    Ensures that max 3 attempts happen, no engine reruns, and fallback occurs.
    """
    # Setup standard mocks for compute
    mock_run_engines.return_value = {
        "customer": {}, "profile": {}, "risk": {}, "plans": {}, 
        "montecarlo": {}, "stress": {}, "cohort": {}, "bundle": {"dummy": "data"}
    }
    
    def run_side_effect(module_name, *args):
        if module_name == "explanation":
            action = run_side_effect.explanation_actions.pop(0)
            if isinstance(action, Exception):
                raise action
            return action
        elif module_name == "verify":
            action = run_side_effect.verify_actions.pop(0)
            return action
        return {}
        
    mock_run.side_effect = run_side_effect

    # ---------------------------------------------------------
    # Scenario A & B: Groq BadRequestError on attempt 1, Success on attempt 2
    # ---------------------------------------------------------
    error_response = MagicMock()
    bad_req = groq.BadRequestError("Failed to validate JSON", response=error_response, body={})
    
    run_side_effect.explanation_actions = [
        bad_req, 
        {"plans_text": "success"} # Attempt 2 succeeds
    ]
    run_side_effect.verify_actions = [
        {"status": "pass"} # Attempt 2 verifies
    ]
    
    s = run_stages("C001")
    
    assert mock_run.call_count == 3
    assert mock_run.call_args_list[0][0][0] == "explanation"
    assert mock_run.call_args_list[1][0][0] == "explanation"
    assert "API Generation Error" in mock_run.call_args_list[1][0][2][0]
    assert mock_run.call_args_list[2][0][0] == "verify"
    
    assert mock_run_engines.call_count == 1
    
    # ---------------------------------------------------------
    # Scenario C, D, E, F: BadRequestError on all 3 attempts -> fallback invoked
    # ---------------------------------------------------------
    mock_run.reset_mock()
    mock_run_engines.reset_mock()
    
    run_side_effect.explanation_actions = [bad_req, bad_req, bad_req]
    run_side_effect.verify_actions = [
        {"status": "pass"} # verify the fallback
    ]
    
    s = run_stages("C001")
    
    assert mock_run_engines.call_count == 1
    
    expl_calls = [call for call in mock_run.call_args_list if call[0][0] == "explanation"]
    assert len(expl_calls) == 3
    
    assert "numbers_used" in s["explanation"]
    
    expl_str = json.dumps(s["explanation"])
    assert "Failed to validate JSON" not in expl_str

@patch("orchestrator.pipeline.run_engines")
@patch("orchestrator.pipeline.run")
def test_valueerror_retry_logic(mock_run, mock_run_engines):
    """
    Tests that a structural ValueError from Explanation agent correctly
    triggers a retry and fallback without crashing.
    """
    mock_run_engines.return_value = {
        "customer": {}, "profile": {}, "risk": {}, "plans": {}, 
        "montecarlo": {}, "stress": {}, "cohort": {}, "bundle": {"dummy": "data"}
    }
    
    def run_side_effect(module_name, *args):
        if module_name == "explanation":
            action = run_side_effect.explanation_actions.pop(0)
            if isinstance(action, Exception):
                raise action
            return action
        elif module_name == "verify":
            action = run_side_effect.verify_actions.pop(0)
            return action
        return {}
        
    mock_run.side_effect = run_side_effect

    # Attempt 1: ValueError, Attempt 2: Success
    value_error = ValueError("Plan ID mismatch. Expected exactly ['A', 'B', 'C'], but got ['A', 'B']")
    run_side_effect.explanation_actions = [value_error, {"plans_text": "success"}]
    run_side_effect.verify_actions = [{"status": "pass"}]
    
    s = run_stages("C001")
    
    assert mock_run.call_count == 3
    assert mock_run_engines.call_count == 1
    assert "Plan ID mismatch" in mock_run.call_args_list[1][0][2][0]

    # Attempt 1-3: ValueError -> Fallback
    mock_run.reset_mock()
    mock_run_engines.reset_mock()
    
    run_side_effect.explanation_actions = [value_error, value_error, value_error]
    run_side_effect.verify_actions = [{"status": "pass"}]
    
    s = run_stages("C001")
    
    assert mock_run_engines.call_count == 1
    expl_calls = [call for call in mock_run.call_args_list if call[0][0] == "explanation"]
    assert len(expl_calls) == 3
    assert "numbers_used" in s["explanation"]
