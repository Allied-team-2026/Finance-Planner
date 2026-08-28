import json

def build_challenger_payload(bundle, explanation, verification):
    """
    Transforms the internal bundle, explanation, and verification results into
    the exact trimmed structure required by the Challenger Agent.
    """
    payload = {
        "context": bundle.get("context", {}),
        "profile": bundle.get("profile", {}),
        "risk": bundle.get("risk", {}),
        "goals": bundle.get("goals", []),
        "plans": bundle.get("plans", []),
        "comparisons": bundle.get("comparisons", {}),
        "n_simulations": bundle.get("n_simulations"),
        "peer_cohort": bundle.get("peer_cohort"),
        "explanation": explanation,
        "verification": verification
    }
        
    forbidden_keys = {
        "customer_id", "name", "customer_name", "account_numbers", 
        "transactions", "investment_events", "individual_peers", 
        "ground_truth_risk"
    }
    
    def clean(obj):
        if isinstance(obj, dict):
            return {k: clean(v) for k, v in obj.items() if k not in forbidden_keys}
        elif isinstance(obj, list):
            return [clean(v) for v in obj]
        return obj

    return clean(payload)
