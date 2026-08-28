import pytest
from models.risk_c001_diagnostic import run_diagnostic

def test_diagnostic_is_deterministic():
    """Diagnostic outputs should be completely deterministic."""
    d1 = run_diagnostic()
    d2 = run_diagnostic()
    
    assert d1["c001_features"] == d2["c001_features"]
    assert d1["c001_prediction"] == d2["c001_prediction"]
    assert d1["synth_features"] == d2["synth_features"]
    assert d1["synth_prediction"] == d2["synth_prediction"]

def test_diagnostic_reports_incomplete_history():
    """Ensure the diagnostic highlights the 0 values caused by the single-month mock."""
    res = run_diagnostic()
    features = res["c001_features"]
    
    assert features["expense_volatility"] == 0.0, "C001 has only 1 month of data, volatility must be 0"
    assert features["budget_overshoot_rate"] == 0.0, "C001 has only 1 month of data, overshoot must be 0"
    
    assert res["c001_prediction"]["revealed_risk"] == "conservative", "The premise of the diagnostic is that C001 predicts conservative"
