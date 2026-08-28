"""
Peer Cohort matching/filtering layer (§16).
"""

def age_band(age):
    if age <= 25:
        return "22-25"
    if age <= 30:
        return "26-30"
    if age <= 35:
        return "31-35"
    if age <= 40:
        return "36-40"
    if age <= 50:
        return "41-50"
    return "51+"

def income_band(income):
    if income <= 50000:
        return "0-50000"
    if income <= 100000:
        return "50000-100000"
    if income <= 150000:
        return "100000-150000"
    if income <= 250000:
        return "150000-250000"
    return "250000+"

def get_priority_1_goal(customer):
    for goal in customer.get("goals", []):
        if goal.get("priority") == 1:
            return goal.get("name")
    return None

def match_cohort(customers, customer, stated_risk):
    """
    Match a customer against the generated customer dataset.
    
    Returns:
        dict: {
            "matched_on": list of keys used,
            "peers": list of matched customer records,
            "cohort_size": int
        }
        or None if < 20 matches found after all fallbacks.
    """
    c_age_band = age_band(customer.get("age", 0))
    # We might need to compute income from profile or it might be passed?
    # The instruction says "income_band(monthly_income)"
    # A customer record typically doesn't have monthly_income directly; profile does.
    # But wait, synthetic_data generates customers with monthly_income?
    # Let's check `customer` dict. In `synthetic_data.py`, customer has `monthly_income`.
    c_income_band = income_band(customer.get("monthly_income", 0))
    c_goal_type = get_priority_1_goal(customer)
    c_stated_risk = stated_risk
    
    def matches(peer, check_goal, check_risk):
        if age_band(peer.get("age", 0)) != c_age_band:
            return False
        if income_band(peer.get("monthly_income", 0)) != c_income_band:
            return False
        if check_goal and get_priority_1_goal(peer) != c_goal_type:
            return False
        if check_risk and peer.get("stated_risk") != c_stated_risk:
            return False
        return True

    # 1. Full 4-key match
    peers = [p for p in customers if matches(p, check_goal=True, check_risk=True)]
    if len(peers) >= 20:
        return {
            "matched_on": ["age_band", "income_band", "goal_type", "stated_risk"],
            "peers": peers,
            "cohort_size": len(peers)
        }
        
    # 2. Fallback 1: remove stated_risk
    peers = [p for p in customers if matches(p, check_goal=True, check_risk=False)]
    if len(peers) >= 20:
        return {
            "matched_on": ["age_band", "income_band", "goal_type"],
            "peers": peers,
            "cohort_size": len(peers)
        }
        
    # 3. Fallback 2: remove goal_type
    peers = [p for p in customers if matches(p, check_goal=False, check_risk=False)]
    if len(peers) >= 20:
        return {
            "matched_on": ["age_band", "income_band"],
            "peers": peers,
            "cohort_size": len(peers)
        }
        
    return None

import statistics

def calculate_cohort_statistics(matched_customers, customer):
    """
    Calculate savings and surplus statistics for the cohort.
    
    Args:
        matched_customers (list): The list of matched peer dicts.
        customer (dict): The target customer's profile dict.
        
    Returns:
        dict: Four numeric cohort outputs.
    """
    c_income = customer.get("monthly_income", 0)
    c_surplus = customer.get("monthly_surplus", 0)
    
    if c_income <= 0:
        raise ValueError("Customer monthly income must be strictly positive.")
        
    customer_savings_rate = c_surplus / c_income
    
    peer_surpluses = []
    peer_rates = []
    
    for p in matched_customers:
        p_income = p.get("monthly_income", 0)
        p_surplus = p.get("monthly_surplus", 0)
        if p_income <= 0:
            raise ValueError("Peer monthly income must be strictly positive.")
            
        peer_surpluses.append(p_surplus)
        peer_rates.append(p_surplus / p_income)
        
    median_surplus = statistics.median(peer_surpluses)
    median_rate = statistics.median(peer_rates)
    
    # Percentile convention: percentage of peers strictly less than the customer's rate,
    # plus half the percentage of peers equal to the customer's rate. 
    # This is standard "rank" percentile which gracefully handles ties and bounds.
    less_than = sum(1 for r in peer_rates if r < customer_savings_rate)
    equal_to = sum(1 for r in peer_rates if r == customer_savings_rate)
    percentile = (less_than + 0.5 * equal_to) / len(peer_rates) * 100
    
    return {
        "median_monthly_surplus": median_surplus,
        "median_savings_rate": median_rate,
        "customer_savings_rate": customer_savings_rate,
        "savings_rate_percentile": percentile
    }
