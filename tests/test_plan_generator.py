import pytest
from engines.plan_generator import effective_equity_ceiling, _load_assumptions

def test_assumptions_loaded():
    assumptions = _load_assumptions()
    assert "risk_profiles" in assumptions
    assert "conservative" in assumptions["risk_profiles"]
    assert "age_equity_bands" in assumptions
    assert "horizon_equity_limits" in assumptions

def test_c001_effective_ceiling():
    profile = {"age": 28, "risk_capacity": "moderate"}
    risk = {"revealed_risk": "moderate"}
    goals = [{"years": 5}, {"years": 12}]
    
    # age 28 -> max 0.85
    # moderate/moderate -> base 0.65
    # horizon 5 -> max 0.65
    # min(0.85, 0.65, 0.65) = 0.65
    assert effective_equity_ceiling(profile, risk, goals) == 0.65

def test_contrast_1_short_horizon():
    # Young, aggressive, but very short horizon
    profile = {"age": 30, "risk_capacity": "aggressive"}
    risk = {"revealed_risk": "aggressive"}
    goals = [{"years": 2}, {"years": 10}]
    
    # age 30 -> max 0.85
    # agg/agg -> base 0.85
    # horizon 2 -> max 0.40
    # min(0.85, 0.85, 0.40) = 0.40
    assert effective_equity_ceiling(profile, risk, goals) == 0.40

def test_contrast_2_old_age():
    # Old, aggressive, long horizon
    profile = {"age": 65, "risk_capacity": "aggressive"}
    risk = {"revealed_risk": "aggressive"}
    goals = [{"years": 20}]
    
    # age 65 -> max 0.40
    # agg/agg -> base 0.85
    # horizon 20 -> max 0.85
    # min(0.40, 0.85, 0.85) = 0.40
    assert effective_equity_ceiling(profile, risk, goals) == 0.40

def test_contrast_3_conservative_risk():
    # Young, long horizon, but capacity is conservative
    profile = {"age": 25, "risk_capacity": "conservative"}
    risk = {"revealed_risk": "moderate"}
    goals = [{"years": 15}]
    
    # age 25 -> max 0.85
    # cons/mod -> base 0.40 (stricter of the two)
    # horizon 15 -> max 0.85
    # min(0.85, 0.40, 0.85) = 0.40
    assert effective_equity_ceiling(profile, risk, goals) == 0.40
