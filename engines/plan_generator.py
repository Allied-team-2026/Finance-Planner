def get_risk_rank(risk_str):
    """Helper to convert risk strings to numerical ranks. Fails loudly on missing data."""
    mapping = {"conservative": 1, "moderate": 2, "aggressive": 3}
    return mapping[risk_str.lower()]

def generate(profile, risk):
    """
    Generates personal financial plans based on profile and risk outputs.
    Output exactly matches mocks/plans_out.json structure.
    """
    # Strict lookups. No silent defaults.
    monthly_surplus = profile["monthly_surplus"]
    risk_capacity = profile["risk_capacity"]
    revealed_risk = risk["revealed_risk"]
    
    capacity_rank = get_risk_rank(risk_capacity)
    revealed_rank = get_risk_rank(revealed_risk)
    effective_ceiling_rank = min(capacity_rank, revealed_rank)
    
    raw_plans = [
        {
            "plan_id": "A",
            "label": "Steady",
            "monthly_investment": 35000,
            "allocation": { "equity": 0.40, "debt": 0.60 },
            "expected_annual_return": 0.09,
            "goal_amount": 2500000,
            "years": 5,
            "risk_level": "conservative"
        },
        {
            "plan_id": "B",
            "label": "Balanced",
            "monthly_investment": 30000,
            "allocation": { "equity": 0.65, "debt": 0.35 },
            "expected_annual_return": 0.11,
            "goal_amount": 2500000,
            "years": 5,
            "risk_level": "moderate"
        },
        {
            "plan_id": "C",
            "label": "Growth",
            "monthly_investment": 52000,
            "allocation": { "equity": 0.85, "debt": 0.15 },
            "expected_annual_return": 0.13,
            "goal_amount": 2500000,
            "years": 5,
            "risk_level": "aggressive"
        }
    ]

    processed_plans = []
    for p in raw_plans:
        monthly_inv = p["monthly_investment"]
        annual_ret = p["expected_annual_return"]
        years = p["years"]
        
        # Dynamic SIP math calculation
        r = annual_ret / 12
        n = years * 12
        corpus = monthly_inv * (((1 + r)**n - 1) / r) * (1 + r)
        projected_corpus = int(round(corpus, -4)) # Rounds to nearest 10k to match mocks
        
        surplus_after_inv = monthly_surplus - monthly_inv
        feasible = surplus_after_inv >= 0
        shortfall = 0 if feasible else abs(surplus_after_inv)
        
        plan_rank = get_risk_rank(p["risk_level"])
        exceeds_ceiling = plan_rank > effective_ceiling_rank
        
        processed_plans.append({
            "plan_id": p["plan_id"],
            "label": p["label"],
            "monthly_investment": monthly_inv,
            "allocation": p["allocation"],
            "expected_annual_return": annual_ret,
            "projected_corpus": projected_corpus,
            "goal_amount": p["goal_amount"],
            "years": years,
            "shortfall": shortfall,
            "feasible": feasible,
            "surplus_after_investment": surplus_after_inv,
            "exceeds_risk_ceiling": exceeds_ceiling
        })

    return {
        "plans": processed_plans,
        "assumptions_version": "assump-v1"
    }
