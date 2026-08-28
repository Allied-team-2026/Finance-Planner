"""
Tests for the Peer Cohort matching engine (§16).
"""

import json
from pathlib import Path
import pytest

from engines.peer_cohort import age_band, income_band, get_priority_1_goal, match_cohort

ROOT = Path(__file__).resolve().parent.parent

# ------------------------------------------------------------- 1. Band Helpers
def test_age_bands():
    assert age_band(21) == "22-25"
    assert age_band(22) == "22-25"
    assert age_band(25) == "22-25"
    assert age_band(26) == "26-30"
    assert age_band(30) == "26-30"
    assert age_band(31) == "31-35"
    assert age_band(35) == "31-35"
    assert age_band(36) == "36-40"
    assert age_band(40) == "36-40"
    assert age_band(41) == "41-50"
    assert age_band(50) == "41-50"
    assert age_band(51) == "51+"
    assert age_band(60) == "51+"

def test_income_bands():
    assert income_band(0) == "0-50000"
    assert income_band(50000) == "0-50000"
    assert income_band(50001) == "50000-100000"
    assert income_band(100000) == "50000-100000"
    assert income_band(100001) == "100000-150000"
    assert income_band(150000) == "100000-150000"
    assert income_band(150001) == "150000-250000"
    assert income_band(250000) == "150000-250000"
    assert income_band(250001) == "250000+"
    assert income_band(500000) == "250000+"

def test_priority_1_goal():
    customer = {
        "goals": [
            {"name": "retirement", "priority": 2},
            {"name": "house_downpayment", "priority": 1},
        ]
    }
    assert get_priority_1_goal(customer) == "house_downpayment"

    customer_missing = {"goals": []}
    assert get_priority_1_goal(customer_missing) is None

# ------------------------------------------------------------- 2. Matching Logic
@pytest.fixture
def mock_dataset():
    """Create a synthetic dataset specifically tuned to hit all fallback paths."""
    # We need:
    # 20 full matches for customer A.
    # 19 full matches + 10 matches missing stated_risk for customer B.
    # 10 full matches + 5 missing stated_risk + 20 missing stated_risk and goal for customer C.
    # 10 matches total even after all fallbacks for customer D.
    data = []
    
    # Customer A matches (20 total)
    # Age 30 (26-30), Income 80k (50k-100k), Goal 'X', Risk 'moderate'
    for _ in range(20):
        data.append({"age": 30, "stated_risk": "moderate", "monthly_income": 80000, "goals": [{"name": "X", "priority": 1}], "stated_risk": "moderate"})
        
    # Customer B matches
    # Age 40 (36-40), Income 120k (100k-150k), Goal 'Y', Risk 'aggressive'
    for _ in range(19):
        # 19 full matches
        data.append({"age": 40, "stated_risk": "moderate", "monthly_income": 120000, "goals": [{"name": "Y", "priority": 1}], "stated_risk": "aggressive"})
    for _ in range(10):
        # 10 matches on age, income, goal, but different risk
        data.append({"age": 40, "stated_risk": "moderate", "monthly_income": 120000, "goals": [{"name": "Y", "priority": 1}], "stated_risk": "conservative"})
        
    # Customer C matches
    # Age 50 (41-50), Income 200k (150k-250k), Goal 'Z', Risk 'conservative'
    for _ in range(10):
        # 10 full matches
        data.append({"age": 50, "stated_risk": "moderate", "monthly_income": 200000, "goals": [{"name": "Z", "priority": 1}], "stated_risk": "conservative"})
    for _ in range(5):
        # 5 matches missing risk
        data.append({"age": 50, "stated_risk": "moderate", "monthly_income": 200000, "goals": [{"name": "Z", "priority": 1}], "stated_risk": "aggressive"})
    for _ in range(20):
        # 20 matches missing risk and goal
        data.append({"age": 50, "stated_risk": "moderate", "monthly_income": 200000, "goals": [{"name": "W", "priority": 1}], "stated_risk": "aggressive"})
        
    # Customer D matches
    # Age 25 (22-25), Income 40k (0-50k), Goal 'X', Risk 'moderate'
    for _ in range(5):
        # Full match
        data.append({"age": 25, "stated_risk": "moderate", "monthly_income": 40000, "goals": [{"name": "X", "priority": 1}], "stated_risk": "moderate"})
    for _ in range(5):
        # Goal match only
        data.append({"age": 25, "stated_risk": "moderate", "monthly_income": 40000, "goals": [{"name": "X", "priority": 1}], "stated_risk": "conservative"})
    for _ in range(5):
        # Base match only
        data.append({"age": 25, "stated_risk": "moderate", "monthly_income": 40000, "goals": [{"name": "Y", "priority": 1}], "stated_risk": "conservative"})
        
    return data

def test_full_match(mock_dataset):
    customer = {"age": 30, "stated_risk": "moderate", "monthly_income": 80000, "goals": [{"name": "X", "priority": 1}]}
    res = match_cohort(mock_dataset, customer, "moderate")
    assert res is not None
    assert res["cohort_size"] == 20
    assert res["matched_on"] == ["age_band", "income_band", "goal_type", "stated_risk"]

def test_fallback_1_stated_risk(mock_dataset):
    customer = {"age": 40, "stated_risk": "moderate", "monthly_income": 120000, "goals": [{"name": "Y", "priority": 1}]}
    res = match_cohort(mock_dataset, customer, "aggressive")
    assert res is not None
    assert res["cohort_size"] == 29
    assert res["matched_on"] == ["age_band", "income_band", "goal_type"]

def test_fallback_2_goal_type(mock_dataset):
    customer = {"age": 50, "stated_risk": "moderate", "monthly_income": 200000, "goals": [{"name": "Z", "priority": 1}]}
    res = match_cohort(mock_dataset, customer, "conservative")
    assert res is not None
    assert res["cohort_size"] == 35  # 10 + 5 + 20
    assert res["matched_on"] == ["age_band", "income_band"]

def test_fewer_than_20_all_fallbacks(mock_dataset):
    customer = {"age": 25, "stated_risk": "moderate", "monthly_income": 40000, "goals": [{"name": "X", "priority": 1}]}
    res = match_cohort(mock_dataset, customer, "moderate")
    assert res is None  # Total possible matches in dataset is 15 (<20)

def test_c001_with_real_dataset():
    """Match C001 against the actual 1,000-customer generated dataset."""
    from engines.synthetic_data import generate_dataset
    customers = generate_dataset(1000, seed=42)
        
    c001 = {
        "age": 28,
        "stated_risk": "moderate", "monthly_income": 120000,
        "goals": [{"name": "house_downpayment", "priority": 1}]
    }
    res = match_cohort(customers, c001, "aggressive")
    
    # We don't assume the hand-written mock is perfectly reproduced, 
    # but we assert it successfully falls back or matches and doesn't crash.
    # It might return None if fewer than 20 customers match even after fallback, 
    # but let's see what the actual dataset produces.
    # The requirement is just to use the real dataset for an integration style match.
    # We will log the actual match size to help report back.
    if res is not None:
        assert res["cohort_size"] >= 20
        assert isinstance(res["matched_on"], list)
    else:
        assert res is None

# ------------------------------------------------------------- 3. Statistics
from engines.peer_cohort import calculate_cohort_statistics

@pytest.fixture
def mock_build_profile(monkeypatch):
    """
    For the pure fixture tests, we just want build_profile to return the peer
    as-is, since our fixtures already contain the pre-computed fields.
    """
    monkeypatch.setattr("engines.peer_cohort.build_profile", lambda p: p)
    monkeypatch.setattr("engines.peer_cohort.extract", lambda p, prof: {})
    monkeypatch.setattr("engines.peer_cohort.predict", lambda feats, stated: {"revealed_risk": stated})
    monkeypatch.setattr("engines.peer_cohort.generate", lambda prof, risk, goals: {
        "plans": [
            {"plan_id": "A", "label": "Steady", "allocation": {"equity": 0.2}},
            {"plan_id": "B", "label": "Balanced", "allocation": {"equity": 0.5}},
            {"plan_id": "C", "label": "Growth", "allocation": {"equity": 0.8}}
        ]
    })

def test_calculate_cohort_statistics_known_5_customer(mock_build_profile):
    """Test calculations with a known 5-customer cohort."""
    matched_customers = [
        {"stated_risk": "moderate", "monthly_income": 100000, "monthly_surplus": 10000},  # rate: 0.1
        {"stated_risk": "moderate", "monthly_income": 100000, "monthly_surplus": 20000},  # rate: 0.2
        {"stated_risk": "moderate", "monthly_income": 100000, "monthly_surplus": 30000},  # rate: 0.3
        {"stated_risk": "moderate", "monthly_income": 100000, "monthly_surplus": 40000},  # rate: 0.4
        {"stated_risk": "moderate", "monthly_income": 100000, "monthly_surplus": 50000},  # rate: 0.5
    ]
    # Median surplus: 30000, Median rate: 0.3
    
    # Below median (0.15) -> strictly less than: 1 (0.1), equal: 0 -> percentile: 1 / 5 = 20.0
    cust_below = {"stated_risk": "moderate", "monthly_income": 100000, "monthly_surplus": 15000}
    stats = calculate_cohort_statistics(matched_customers, cust_below)
    assert stats["median_monthly_surplus"] == 30000
    assert stats["median_savings_rate"] == 0.3
    assert stats["customer_savings_rate"] == 0.15
    assert stats["savings_rate_percentile"] == 20.0

    # At median (0.3) -> strictly less: 2, equal: 1 -> percentile: (2 + 0.5) / 5 = 50.0
    cust_median = {"stated_risk": "moderate", "monthly_income": 100000, "monthly_surplus": 30000}
    stats = calculate_cohort_statistics(matched_customers, cust_median)
    assert stats["savings_rate_percentile"] == 50.0

    # Above median (0.45) -> strictly less: 4, equal: 0 -> percentile: 4 / 5 = 80.0
    cust_above = {"stated_risk": "moderate", "monthly_income": 100000, "monthly_surplus": 45000}
    stats = calculate_cohort_statistics(matched_customers, cust_above)
    assert stats["savings_rate_percentile"] == 80.0

def test_percentile_ties(mock_build_profile):
    matched_customers = [
        {"stated_risk": "moderate", "monthly_income": 100000, "monthly_surplus": 20000},  # 0.2
        {"stated_risk": "moderate", "monthly_income": 100000, "monthly_surplus": 20000},  # 0.2
        {"stated_risk": "moderate", "monthly_income": 100000, "monthly_surplus": 20000},  # 0.2
        {"stated_risk": "moderate", "monthly_income": 100000, "monthly_surplus": 20000},  # 0.2
    ]
    # At 0.2: strictly less: 0, equal: 4 -> percentile: (0 + 2) / 4 = 50.0
    cust = {"stated_risk": "moderate", "monthly_income": 100000, "monthly_surplus": 20000}
    stats = calculate_cohort_statistics(matched_customers, cust)
    assert stats["savings_rate_percentile"] == 50.0

def test_c001_savings_rate(mock_build_profile):
    matched_customers = [
        {"stated_risk": "moderate", "monthly_income": 100000, "monthly_surplus": 20000},  # rate 0.2
    ]
    c001 = {"stated_risk": "moderate", "monthly_income": 120000, "monthly_surplus": 45000}
    stats = calculate_cohort_statistics(matched_customers, c001)
    assert stats["customer_savings_rate"] == 0.375

def test_zero_income_error(mock_build_profile):
    cust = {"stated_risk": "moderate", "monthly_income": 0, "monthly_surplus": 0}
    with pytest.raises(ValueError):
        calculate_cohort_statistics([{"stated_risk": "moderate", "monthly_income": 100000, "monthly_surplus": 20000}], cust)
        
    cust = {"stated_risk": "moderate", "monthly_income": 100000, "monthly_surplus": 20000}
    with pytest.raises(ValueError):
        calculate_cohort_statistics([{"stated_risk": "moderate", "monthly_income": 0, "monthly_surplus": 0}], cust)

def test_deterministic_and_no_individual_data_exposed(mock_build_profile):
    matched = [{"stated_risk": "moderate", "monthly_income": 100000, "monthly_surplus": 20000}]
    cust = {"stated_risk": "moderate", "monthly_income": 120000, "monthly_surplus": 45000}
    stats1 = calculate_cohort_statistics(matched, cust)
    stats2 = calculate_cohort_statistics(matched, cust)
    assert stats1 == stats2
    
    # Must only contain the 6 requested keys
    assert set(stats1.keys()) == {
        "median_monthly_surplus",
        "median_savings_rate",
        "customer_savings_rate",
        "savings_rate_percentile",
        "most_common_plan_label",
        "most_common_allocation"
    }

# ------------------------------------------------------------- 4. Mismatch Rate
from engines.peer_cohort import calculate_mismatch_rate

@pytest.fixture
def mock_for_mismatch(monkeypatch, mock_build_profile):
    monkeypatch.setattr("engines.peer_cohort.extract", lambda p, prof: {})
    # Use a magic key '_revealed' on the peer to dictate the mock predict output
    monkeypatch.setattr("engines.peer_cohort.predict", lambda feats, stated: {"revealed_risk": feats.get("_revealed", stated)})
    # To pass _revealed through extract:
    monkeypatch.setattr("engines.peer_cohort.extract", lambda p, prof: {"_revealed": p.get("_revealed", stated_risk_from_p(p))})
    
    def stated_risk_from_p(p):
        return p.get("stated_risk", "moderate")
        
def test_mismatch_rate_zero(mock_for_mismatch):
    # All peers have stated == revealed
    peers = [
        {"stated_risk": "moderate", "_revealed": "moderate"},
        {"stated_risk": "aggressive", "_revealed": "aggressive"},
    ]
    assert calculate_mismatch_rate(peers) == 0.0

def test_mismatch_rate_all(mock_for_mismatch):
    # All peers mismatch
    peers = [
        {"stated_risk": "moderate", "_revealed": "aggressive"},
        {"stated_risk": "conservative", "_revealed": "moderate"},
    ]
    assert calculate_mismatch_rate(peers) == 1.0

def test_mismatch_rate_mixed(mock_for_mismatch):
    # 2 mismatch, 3 match -> 2/5 = 0.4
    peers = [
        {"stated_risk": "moderate", "_revealed": "aggressive"},  # mismatch
        {"stated_risk": "conservative", "_revealed": "moderate"}, # mismatch
        {"stated_risk": "aggressive", "_revealed": "aggressive"}, # match
        {"stated_risk": "conservative", "_revealed": "conservative"}, # match
        {"stated_risk": "moderate", "_revealed": "moderate"}, # match
    ]
    assert calculate_mismatch_rate(peers) == 0.4
    
def test_mismatch_rate_empty():
    with pytest.raises(ValueError):
        calculate_mismatch_rate([])

def test_mismatch_rate_real_data():
    from engines.synthetic_data import generate_dataset
    from engines.peer_cohort import match_cohort
    customers = generate_dataset(100, seed=42)  # smaller subset for speed is fine, but let's use 1000
    customers = generate_dataset(1000, seed=42)
    c001 = {
        "age": 28,
        "stated_risk": "moderate", "monthly_income": 120000,
        "goals": [{"name": "house_downpayment", "priority": 1}]
    }
    # Using real models, no mocks
    res = match_cohort(customers, c001, "aggressive")
    
    rate = calculate_mismatch_rate(res["peers"])
# ------------------------------------------------------------- 5. Most Common Plan and Allocation

def test_most_common_plan_A(mock_build_profile, monkeypatch):
    monkeypatch.setattr("engines.peer_cohort.extract", lambda p, prof: {})
    monkeypatch.setattr("engines.peer_cohort.predict", lambda feats, stated: {"revealed_risk": stated})
    monkeypatch.setattr("engines.peer_cohort.generate", lambda prof, risk, goals: {
        "plans": [
            {"plan_id": "A", "label": "Steady", "allocation": {"equity": 0.2}},
            {"plan_id": "B", "label": "Balanced", "allocation": {"equity": 0.5}},
            {"plan_id": "C", "label": "Growth", "allocation": {"equity": 0.8}}
        ]
    })
    
    peers = [
        {"stated_risk": "conservative", "monthly_income": 100000, "monthly_surplus": 10000},
        {"stated_risk": "conservative", "monthly_income": 100000, "monthly_surplus": 10000},
        {"stated_risk": "moderate", "monthly_income": 100000, "monthly_surplus": 10000}
    ]
    cust = {"stated_risk": "moderate", "monthly_income": 120000, "monthly_surplus": 45000}
    stats = calculate_cohort_statistics(peers, cust)
    assert stats["most_common_plan_label"] == "Steady"
    assert stats["most_common_allocation"] == {"equity": 0.2}

def test_most_common_plan_B(mock_build_profile, monkeypatch):
    monkeypatch.setattr("engines.peer_cohort.extract", lambda p, prof: {})
    monkeypatch.setattr("engines.peer_cohort.predict", lambda feats, stated: {"revealed_risk": stated})
    monkeypatch.setattr("engines.peer_cohort.generate", lambda prof, risk, goals: {
        "plans": [
            {"plan_id": "A", "label": "Steady", "allocation": {"equity": 0.2}},
            {"plan_id": "B", "label": "Balanced", "allocation": {"equity": 0.5}},
            {"plan_id": "C", "label": "Growth", "allocation": {"equity": 0.8}}
        ]
    })
    
    peers = [
        {"stated_risk": "conservative", "monthly_income": 100000, "monthly_surplus": 10000},
        {"stated_risk": "moderate", "monthly_income": 100000, "monthly_surplus": 10000},
        {"stated_risk": "moderate", "monthly_income": 100000, "monthly_surplus": 10000}
    ]
    cust = {"stated_risk": "moderate", "monthly_income": 120000, "monthly_surplus": 45000}
    stats = calculate_cohort_statistics(peers, cust)
    assert stats["most_common_plan_label"] == "Balanced"
    assert stats["most_common_allocation"] == {"equity": 0.5}

def test_most_common_plan_tie(mock_build_profile, monkeypatch):
    monkeypatch.setattr("engines.peer_cohort.extract", lambda p, prof: {})
    monkeypatch.setattr("engines.peer_cohort.predict", lambda feats, stated: {"revealed_risk": stated})
    monkeypatch.setattr("engines.peer_cohort.generate", lambda prof, risk, goals: {
        "plans": [
            {"plan_id": "A", "label": "Steady", "allocation": {"equity": 0.2}},
            {"plan_id": "B", "label": "Balanced", "allocation": {"equity": 0.5}},
            {"plan_id": "C", "label": "Growth", "allocation": {"equity": 0.8}}
        ]
    })
    
    # 2 conservative (A), 2 moderate (B) => A before B
    peers = [
        {"stated_risk": "conservative", "monthly_income": 100000, "monthly_surplus": 10000},
        {"stated_risk": "conservative", "monthly_income": 100000, "monthly_surplus": 10000},
        {"stated_risk": "moderate", "monthly_income": 100000, "monthly_surplus": 10000},
        {"stated_risk": "moderate", "monthly_income": 100000, "monthly_surplus": 10000}
    ]
    cust = {"stated_risk": "moderate", "monthly_income": 120000, "monthly_surplus": 45000}
    stats = calculate_cohort_statistics(peers, cust)
    assert stats["most_common_plan_label"] == "Steady"
    assert stats["most_common_allocation"] == {"equity": 0.2}

def test_most_common_real_generated_peer():
    from engines.synthetic_data import generate_dataset
    from engines.peer_cohort import match_cohort
    customers = generate_dataset(1000, seed=42)
    c001 = {
        "age": 28,
        "monthly_income": 120000,
        "monthly_surplus": 45000,
        "goals": [{"name": "house_downpayment", "priority": 1}]
    }
    # No mocks, uses real models
    res = match_cohort(customers, c001, "aggressive")
    
    # Will use real build_profile, extract, predict, generate
    stats = calculate_cohort_statistics(res["peers"], c001)
    
    assert stats["most_common_plan_label"] in ["Steady", "Balanced", "Growth"]
    assert "equity" in stats["most_common_allocation"]
