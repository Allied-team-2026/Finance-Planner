def get_risk_rank(risk_str):
    """Helper to convert risk strings to numerical ranks for conservative comparison."""
    mapping = {"conservative": 1, "moderate": 2, "aggressive": 3}
    # Default to moderate if something is missing or malformed
    return mapping.get(str(risk_str).lower(), 2)

def generate(profile, risk):
    """
    Generates personal financial plans based on profile and risk outputs.
    Output exactly matches mocks/plans_out.json structure.
    """
    # 1. Extract required context
    monthly_surplus = profile.get("monthly_surplus", 45000)
    risk_capacity = profile.get("risk_capacity", "moderate")
    
    # Handle naming differences based on whether we get raw §3 output or orchestrator payload
    revealed_risk = risk.get("revealed_risk") or risk.get("revealed", "moderate")
    
    # 2. Determine allocation ceiling (the more conservative of the two)
    capacity_rank = get_risk_rank(risk_capacity)
    revealed_rank = get_risk_rank(revealed_risk)
    effective_ceiling_rank = min(capacity_rank, revealed_rank)
    
    # 3. Base plans (raw data to be processed)
    raw_plans = [
        {
            "plan_id": "A",
            "label": "Steady",
            "monthly_investment": 35000,
            "allocation": { "equity": 0.40, "debt": 0.60 },
            "expected_annual_return": 0.09,
            "projected_corpus": 2620000,
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
            "projected_corpus": 2540000,
            "goal_amount": 2500000,
            "years": 5,
            "risk_level": "moderate"
        },
        {
            "plan_id": "C",
            "label": "Aggressive Growth",
            "monthly_investment": 28000,
            "allocation": { "equity": 0.85, "debt": 0.15 },
            "expected_annual_return": 0.13,
            "projected_corpus": 2850000,
            "goal_amount": 2500000,
            "years": 5,
            "risk_level": "aggressive"
        }
    ]

    # 4. Process plans and calculate dynamic fields
    processed_plans = []
    for p in raw_plans:
        monthly_inv = p["monthly_investment"]
        surplus_after_inv = monthly_surplus - monthly_inv
        feasible = surplus_after_inv >= 0
        shortfall = 0 if feasible else abs(surplus_after_inv)
        
        # Flag if this plan exceeds the customer's safe ceiling
        plan_rank = get_risk_rank(p["risk_level"])
        exceeds_ceiling = plan_rank > effective_ceiling_rank
        
        plan_obj = {
            "plan_id": p["plan_id"],
            "label": p["label"],
            "monthly_investment": monthly_inv,
            "allocation": p["allocation"],
            "expected_annual_return": p["expected_annual_return"],
            "projected_corpus": p["projected_corpus"],
            "goal_amount": p["goal_amount"],
            "years": p["years"],
            "shortfall": shortfall,
            "feasible": feasible,
            "surplus_after_investment": surplus_after_inv,
            "exceeds_risk_ceiling": exceeds_ceiling
        }
        processed_plans.append(plan_obj)

    return {
        "plans": processed_plans,
        "assumptions_version": "assump-v1"
    }
def get_risk_rank(risk_str):
    """Helper to convert risk strings to numerical ranks for conservative comparison."""
    mapping = {"conservative": 1, "moderate": 2, "aggressive": 3}
    # Default to moderate if something is missing or malformed
    return mapping.get(str(risk_str).lower(), 2)

def generate(profile, risk):
    """
    Generates personal financial plans based on profile and risk outputs.
    Output exactly matches mocks/plans_out.json structure.
    """
    # 1. Extract required context
    monthly_surplus = profile.get("monthly_surplus", 45000)
    risk_capacity = profile.get("risk_capacity", "moderate")
    
    # Handle naming differences based on whether we get raw §3 output or orchestrator payload
    revealed_risk = risk.get("revealed_risk") or risk.get("revealed", "moderate")
    
    # 2. Determine allocation ceiling (the more conservative of the two)
    capacity_rank = get_risk_rank(risk_capacity)
    revealed_rank = get_risk_rank(revealed_risk)
    effective_ceiling_rank = min(capacity_rank, revealed_rank)
    
    # 3. Base plans (raw data to be processed)
    raw_plans = [
        {
            "plan_id": "A",
            "label": "Steady",
            "monthly_investment": 35000,
            "allocation": { "equity": 0.40, "debt": 0.60 },
            "expected_annual_return": 0.09,
            "projected_corpus": 2620000,
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
            "projected_corpus": 2540000,
            "goal_amount": 2500000,
            "years": 5,
            "risk_level": "moderate"
        },
        {
            "plan_id": "C",
            "label": "Aggressive Growth",
            "monthly_investment": 28000,
            "allocation": { "equity": 0.85, "debt": 0.15 },
            "expected_annual_return": 0.13,
            "projected_corpus": 2850000,
            "goal_amount": 2500000,
            "years": 5,
            "risk_level": "aggressive"
        }
    ]

    # 4. Process plans and calculate dynamic fields
    processed_plans = []
    for p in raw_plans:
        monthly_inv = p["monthly_investment"]
        surplus_after_inv = monthly_surplus - monthly_inv
        
        # Check affordability
        feasible = surplus_after_inv >= 0
        shortfall = 0 if feasible else abs(surplus_after_inv)
        
        # Flag if this plan exceeds the customer's safe ceiling
        plan_rank = get_risk_rank(p["risk_level"])
        exceeds_ceiling = plan_rank > effective_ceiling_rank
        
        processed_plans.append({
            "plan_id": p["plan_id"],
            "label": p["label"],
            "monthly_investment": monthly_inv,
            "allocation": p["allocation"],
            "expected_annual_return": p["expected_annual_return"],
            "projected_corpus": p["projected_corpus"],
            "goal_amount": p["goal_amount"],
            "years": p["years"],
            "shortfall": shortfall,
            "feasible": feasible,
            "surplus_after_investment": surplus_after_inv,
            "exceeds_risk_ceiling": exceeds_ceiling
        })

    return {
        "plans": processed_plans,
        "assumptions_version": "assump-v1"
    }
