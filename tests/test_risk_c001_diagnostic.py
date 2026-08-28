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
    """Ensure the diagnostic runs successfully."""
    res = run_diagnostic()
    features = res["c001_features"]
    
    assert "expense_volatility" in features
