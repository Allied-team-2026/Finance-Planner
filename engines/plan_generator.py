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
