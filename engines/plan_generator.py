# engines/plan_generator.py

def generate(profile, risk):
    """
    Plan Generator (§4)
    Owner: Pushkar
    In: Profile output + Risk output
    Out: Dictionary matching mocks/plans_out.json
    """
    monthly_surplus = profile.get("monthly_surplus", 45000)
    
    # Define a sample plan output matching your contract/mocks
    plans = [
        {
            "plan_id": "A",
            "label": "Steady",
            "monthly_investment": 35000,
            "allocation": { "equity": 0.40, "debt": 0.60 },
            "expected_annual_return": 0.09,
            "projected_corpus": 2620000,
            "goal_amount": 2500000,
            "years": 5,
            "shortfall": 0,
            "feasible": True,
            "surplus_after_investment": monthly_surplus - 35000,
            "exceeds_risk_ceiling": False
        }
    ]

    return {
        "plans": plans,
        "assumptions_version": "assump-v1"
    }
