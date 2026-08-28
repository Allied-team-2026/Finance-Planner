import json
from pathlib import Path

_ASSUMPTIONS = None

def _load_assumptions():
    global _ASSUMPTIONS
    if _ASSUMPTIONS is None:
        path = Path(__file__).resolve().parent.parent / "data" / "assumptions.json"
        data = json.loads(path.read_text())
        
        # Validation
        assert "risk_profiles" in data, "risk_profiles missing from assumptions"
        for rp in ["conservative", "moderate", "aggressive"]:
            assert rp in data["risk_profiles"], f"{rp} missing from risk_profiles"
            
        assert "age_equity_bands" in data, "age_equity_bands missing"
        assert "horizon_equity_limits" in data, "horizon_equity_limits missing"
        
        _ASSUMPTIONS = data
    return _ASSUMPTIONS

def _risk_level_value(risk_str):
    mapping = {"conservative": 1, "moderate": 2, "aggressive": 3}
    return mapping.get(risk_str, 1)

def effective_equity_ceiling(profile, risk, goals):
    """
    Calculate the effective equity ceiling using the stricter of:
    - risk capacity vs revealed risk
    - age equity band
    - shortest goal horizon limit
    """
    assumptions = _load_assumptions()
    
    # 1. More conservative of risk_capacity and revealed_risk
    cap = profile.get("risk_capacity", "conservative")
    rev = risk.get("revealed_risk", "conservative")
    
    val_cap = _risk_level_value(cap)
    val_rev = _risk_level_value(rev)
    
    eff_risk_val = min(val_cap, val_rev)
    eff_risk_str = {1: "conservative", 2: "moderate", 3: "aggressive"}[eff_risk_val]
    
    base_equity = assumptions["risk_profiles"][eff_risk_str]["allocation"]["equity"]
    
    # 2. Age equity band
    age = profile.get("age", 0)
    age_max = 1.0
    for band in assumptions["age_equity_bands"]:
        if age <= band["max_age"]:
            age_max = band["max_equity"]
            break
            
    # 3. Shortest goal horizon limit
    horizon_max = 1.0
    if goals:
        shortest_horizon = min(g["years"] for g in goals)
        for band in assumptions["horizon_equity_limits"]:
            if shortest_horizon <= band["max_years"]:
                horizon_max = band["max_equity"]
                break
                
    # Use the stricter resulting percentage
    return min(base_equity, age_max, horizon_max)

def select_allocation(risk_level, effective_ceiling):
    """
    Select the configured allocation and return for a risk level,
    and flag if it exceeds the effective equity ceiling.
    Does not silently lower the allocation.
    """
    assumptions = _load_assumptions()
    if risk_level not in assumptions["risk_profiles"]:
        raise ValueError(f"Unknown risk level: {risk_level}")
        
    profile = assumptions["risk_profiles"][risk_level]
    
    allocation = profile["allocation"]
    expected_return = profile["expected_annual_return"]
    
    # Strict inequality to determine if it exceeds ceiling
    exceeds = float(allocation["equity"]) > float(effective_ceiling)
    
    return {
        "allocation": dict(allocation),
        "expected_annual_return": expected_return,
        "exceeds_risk_ceiling": exceeds
    }

def projected_corpus(monthly_investment, expected_annual_return, years):
    """
    Calculate the projected corpus using the SIP annuity-due formula.
    Rounds the final result to the nearest 10,000.
    """
    if expected_annual_return == 0:
        raw_corpus = monthly_investment * years * 12
    else:
        r = expected_annual_return / 12.0
        n = years * 12
        raw_corpus = monthly_investment * (((1 + r)**n - 1) / r) * (1 + r)
        
    return int(round(raw_corpus / 10000.0) * 10000)

def calculate_affordability(monthly_surplus, monthly_investment):
    """
    Calculate affordability metrics for a proposed monthly investment.
    Does not clamp negative surplus.
    """
    surplus_after_investment = monthly_surplus - monthly_investment
    shortfall = max(0, monthly_investment - monthly_surplus)
    feasible = monthly_investment <= monthly_surplus
    
    return {
        "surplus_after_investment": surplus_after_investment,
        "shortfall": shortfall,
        "feasible": feasible
    }

def calculate_plan_investments(monthly_surplus):
    """
    Calculate the integer monthly investments for Plan A, B, and C
    using the configured sizing factors in assumptions.
    """
    assumptions = _load_assumptions()
    sizing = assumptions["investment_sizing"]
    
    return {
        "A": int(round(monthly_surplus * sizing["Plan A"])),
        "B": int(round(monthly_surplus * sizing["Plan B"])),
        "C": int(round(monthly_surplus * sizing["Plan C"]))
    }

def generate(profile, risk, goals):
    """
    Generate three base financial plans using Profile, Risk, and Goals outputs.
    Combines assumptions with effective equity ceilings and SIP logic.
    """
    assumptions = _load_assumptions()
    
    # 1. Primary goal
    primary_goal = next((g for g in goals if g.get("priority") == 1), None)
    if not primary_goal:
        raise ValueError("No priority 1 goal found")
        
    # 2. Equity ceiling and investments
    eff_ceiling = effective_equity_ceiling(profile, risk, goals)
    monthly_surplus = profile.get("monthly_surplus", 0)
    investments = calculate_plan_investments(monthly_surplus)
    
    # 3. Create plans
    plan_defs = [
        ("A", "Steady", "conservative"),
        ("B", "Balanced", "moderate"),
        ("C", "Growth", "aggressive")
    ]
    
    plans = []
    for pid, label, risk_lvl in plan_defs:
        alloc_data = select_allocation(risk_lvl, eff_ceiling)
        monthly_inv = investments[pid]
        
        corpus = projected_corpus(monthly_inv, alloc_data["expected_annual_return"], primary_goal["years"])
        affordability = calculate_affordability(monthly_surplus, monthly_inv)
        
        plans.append({
            "plan_id": pid,
            "label": label,
            "monthly_investment": monthly_inv,
            "allocation": alloc_data["allocation"],
            "expected_annual_return": alloc_data["expected_annual_return"],
            "projected_corpus": corpus,
            "goal_amount": primary_goal["amount"],
            "years": primary_goal["years"],
            "shortfall": affordability["shortfall"],
            "feasible": affordability["feasible"],
            "surplus_after_investment": affordability["surplus_after_investment"],
            "exceeds_risk_ceiling": alloc_data["exceeds_risk_ceiling"]
        })
        
    return {
        "assumptions_version": assumptions["assumptions_version"],
        "plans": plans
    }
