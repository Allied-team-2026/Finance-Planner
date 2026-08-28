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

from engines.plan_generator import select_allocation

def test_select_allocation_conservative():
    res = select_allocation("conservative", 0.85)
    assert res["allocation"]["equity"] == 0.40
    assert res["allocation"]["debt"] == 0.60
    assert res["expected_annual_return"] == 0.09
    assert res["exceeds_risk_ceiling"] is False

def test_select_allocation_moderate_under_ceiling():
    res = select_allocation("moderate", 0.85)
    assert res["allocation"]["equity"] == 0.65
    assert res["allocation"]["debt"] == 0.35
    assert res["expected_annual_return"] == 0.11
    assert res["exceeds_risk_ceiling"] is False

def test_select_allocation_aggressive_under_ceiling():
    res = select_allocation("aggressive", 0.90)
    assert res["allocation"]["equity"] == 0.85
    assert res["allocation"]["debt"] == 0.15
    assert res["expected_annual_return"] == 0.13
    assert res["exceeds_risk_ceiling"] is False

def test_select_allocation_aggressive_exceeds_ceiling():
    # aggressive is 0.85 equity. Against ceiling 0.65, it exceeds.
    res = select_allocation("aggressive", 0.65)
    assert res["allocation"]["equity"] == 0.85  # MUST NOT be lowered
    assert res["exceeds_risk_ceiling"] is True

def test_select_allocation_moderate_exactly_on_ceiling():
    # moderate is 0.65 equity. Against ceiling 0.65, it does not exceed.
    res = select_allocation("moderate", 0.65)
    assert res["allocation"]["equity"] == 0.65
    assert res["exceeds_risk_ceiling"] is False

from engines.plan_generator import projected_corpus

def test_projected_corpus_plan_a():
    # Plan A: 35000, 0.09, 5 years -> 2660000
    assert projected_corpus(35000, 0.09, 5) == 2660000

def test_projected_corpus_plan_b():
    # Plan B: 30000, 0.11, 5 years -> 2410000
    assert projected_corpus(30000, 0.11, 5) == 2410000

def test_projected_corpus_plan_c():
    # Plan C: 52000, 0.13, 5 years -> 4410000
    assert projected_corpus(52000, 0.13, 5) == 4410000

from engines.plan_generator import calculate_affordability

def test_calculate_affordability_feasible():
    res = calculate_affordability(45000, 35000)
    assert res["surplus_after_investment"] == 10000
    assert res["shortfall"] == 0
    assert res["feasible"] is True

def test_calculate_affordability_unfeasible():
    res = calculate_affordability(45000, 52000)
    assert res["surplus_after_investment"] == -7000
    assert res["shortfall"] == 7000
    assert res["feasible"] is False

def test_investment_sizing_factors():
    assumptions = _load_assumptions()
    assert "investment_sizing" in assumptions
    sizing = assumptions["investment_sizing"]
    
    surplus = 45000
    plan_a_inv = int(round(surplus * sizing["Plan A"]))
    plan_b_inv = int(round(surplus * sizing["Plan B"]))
    plan_c_inv = int(round(surplus * sizing["Plan C"]))
    
    assert plan_a_inv == 35000
    assert plan_b_inv == 30000
    assert plan_c_inv == 52000

from engines.plan_generator import calculate_plan_investments

def test_calculate_plan_investments_c001():
    res = calculate_plan_investments(45000)
    assert res == {"A": 35000, "B": 30000, "C": 52000}

def test_calculate_plan_investments_20000():
    res = calculate_plan_investments(20000)
    assert res == {"A": 15556, "B": 13333, "C": 23111}

def test_calculate_plan_investments_100000():
    res = calculate_plan_investments(100000)
    assert res == {"A": 77778, "B": 66667, "C": 115556}

def test_calculate_plan_investments_monotonicity():
    surpluses = [10000, 25000, 50000, 80000, 150000]
    prev_a, prev_b, prev_c = 0, 0, 0
    for s in surpluses:
        res = calculate_plan_investments(s)
        assert res["A"] >= prev_a
        assert res["B"] >= prev_b
        assert res["C"] >= prev_c
        prev_a, prev_b, prev_c = res["A"], res["B"], res["C"]

def test_calculate_plan_investments_deterministic():
    res1 = calculate_plan_investments(67890)
    res2 = calculate_plan_investments(67890)
    assert res1 == res2

from engines.plan_generator import generate
import json
from pathlib import Path

def test_generate_c001_matches_mock():
    # Load inputs
    c001_profile = json.loads(Path("mocks/profile_out.json").read_text())
    c001_risk = json.loads(Path("mocks/risk_out.json").read_text())
    c001_raw = json.loads(Path("mocks/customer_C001.json").read_text())
    c001_goals = c001_raw.get("goals", [])
    
    # Generate
    res = generate(c001_profile, c001_risk, c001_goals)
    
    # Assert top-level
    assert res["assumptions_version"] == "assump-v1"
    assert len(res["plans"]) == 3
    
    # Plan A
    pa = res["plans"][0]
    assert pa["plan_id"] == "A"
    assert pa["label"] == "Steady"
    assert pa["monthly_investment"] == 35000
    assert pa["allocation"]["equity"] == 0.40
    assert pa["allocation"]["debt"] == 0.60
    assert pa["expected_annual_return"] == 0.09
    assert pa["projected_corpus"] == 2660000
    assert pa["goal_amount"] == 2500000
    assert pa["years"] == 5
    assert pa["shortfall"] == 0
    assert pa["feasible"] is True
    assert pa["surplus_after_investment"] == 10000
    assert pa["exceeds_risk_ceiling"] is False
    
    # Plan B
    pb = res["plans"][1]
    assert pb["plan_id"] == "B"
    assert pb["label"] == "Balanced"
    assert pb["monthly_investment"] == 30000
    assert pb["allocation"]["equity"] == 0.65
    assert pb["allocation"]["debt"] == 0.35
    assert pb["expected_annual_return"] == 0.11
    assert pb["projected_corpus"] == 2410000
    assert pb["goal_amount"] == 2500000
    assert pb["years"] == 5
    assert pb["shortfall"] == 0
    assert pb["feasible"] is True
    assert pb["surplus_after_investment"] == 15000
    assert pb["exceeds_risk_ceiling"] is False
    
    # Plan C
    pc = res["plans"][2]
    assert pc["plan_id"] == "C"
    assert pc["label"] == "Growth"
    assert pc["monthly_investment"] == 52000
    assert pc["allocation"]["equity"] == 0.85
    assert pc["allocation"]["debt"] == 0.15
    assert pc["expected_annual_return"] == 0.13
    assert pc["projected_corpus"] == 4410000
    assert pc["goal_amount"] == 2500000
    assert pc["years"] == 5
    assert pc["shortfall"] == 7000
    assert pc["feasible"] is False
    assert pc["surplus_after_investment"] == -7000
    assert pc["exceeds_risk_ceiling"] is True
