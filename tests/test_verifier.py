import json
import pytest
from agents.verifier import verify

@pytest.fixture
def valid_bundle():
    return {
        "customer_id": "C001",
        "customer_name": "Rahul Mehta",
        "profile": {
            "risk_capacity": "moderate"
        },
        "risk": {
            "stated": "aggressive",
            "revealed": "moderate"
        },
        "plans": [
            {
                "plan_id": "A",
                "monthly_investment": 35000,
                "allocation": {"equity": 0.40, "debt": 0.60},
                "projected_corpus": 2660000,
                "success_probability": 0.73
            },
            {
                "plan_id": "B",
                "monthly_investment": 30000,
                "allocation": {"equity": 0.65, "debt": 0.35},
                "projected_corpus": 2410000,
                "success_probability": 0.56
            },
            {
                "plan_id": "C",
                "monthly_investment": 52000,
                "allocation": {"equity": 0.85, "debt": 0.15},
                "projected_corpus": 4410000,
                "success_probability": 0.92
            }
        ],
        "goals": [],
        "comparisons": {},
        "peer_cohort": {
            "cohort_size": 20,
            "median_savings_rate": 0.37
        }
    }

@pytest.fixture
def valid_explanation():
    return {
        "plans_text": [
            {
                "plan_id": "A",
                "headline": "Plan A",
                "body": "Invest 35000 for 2,660,000. 40% equity. 73% success.",
                "pros": [],
                "cons": []
            },
            {
                "plan_id": "B",
                "headline": "Plan B",
                "body": "Invest 30,000 for 2410000. 65% equity. 56% success.",
                "pros": [],
                "cons": []
            },
            {
                "plan_id": "C",
                "headline": "Plan C",
                "body": "Invest 52,000 for 4410000. 85% equity. 92% success.",
                "pros": [],
                "cons": []
            }
        ],
        "goal_priority_note": "note",
        "mismatch_note": "stated aggressive but revealed moderate.",
        "peer_cohort_note": "cohort of 20 with 0.37 savings.",
        "numbers_used": [35000, 2660000, 40, 73, 30000, 2410000, 65, 56, 52000, 4410000, 85, 92, 20, 0.37]
    }

def test_valid_explanation_passes(valid_explanation, valid_bundle):
    result = verify(valid_explanation, valid_bundle)
    assert result["status"] == "pass"
    assert result["unverified_numbers"] == []
    assert result["suitability_flags"] == []

def test_fabricated_number_fails(valid_explanation, valid_bundle):
    valid_explanation["plans_text"][0]["body"] += " 99999"
    result = verify(valid_explanation, valid_bundle)
    assert result["status"] == "fail"
    assert "99999" in str(result["unverified_numbers"])

def test_wrong_plan_values_cross_contamination(valid_explanation, valid_bundle):
    # Put Plan B's investment in Plan A without referencing B
    valid_explanation["plans_text"][0]["body"] = "Invest 30000."
    result = verify(valid_explanation, valid_bundle)
    assert result["status"] == "fail"
    assert any("Cross-contamination" in f for f in result["suitability_flags"])

def test_wrong_risk_values_fail(valid_explanation, valid_bundle):
    valid_explanation["mismatch_note"] = "conservative approach."
    result = verify(valid_explanation, valid_bundle)
    assert result["status"] == "fail"
    assert any("Categorical risk violation" in f for f in result["suitability_flags"])

def test_privacy_violation_fails(valid_explanation, valid_bundle):
    valid_explanation["mismatch_note"] = "C001 is the customer."
    result = verify(valid_explanation, valid_bundle)
    assert result["status"] == "fail"
    assert any("Privacy violation" in f for f in result["suitability_flags"])

def test_empty_explanation_fails(valid_bundle):
    result = verify({}, valid_bundle)
    assert result["status"] == "fail"

def test_missing_plan_c_fails(valid_explanation, valid_bundle):
    valid_explanation["plans_text"].pop()
    result = verify(valid_explanation, valid_bundle)
    assert result["status"] == "fail"
    assert any("Expected exactly 3 plans" in f for f in result["suitability_flags"])

def test_forbidden_claim_fails(valid_explanation, valid_bundle):
    valid_explanation["plans_text"][0]["body"] += " I guarantee this will work."
    result = verify(valid_explanation, valid_bundle)
    assert result["status"] == "fail"
    assert any("Forbidden claim" in f for f in result["suitability_flags"])

def test_p10_p90_labels_pass(valid_explanation, valid_bundle):
    # 10 and 90 should be ignored if used structurally
    valid_explanation["plans_text"][0]["body"] += " 10th percentile and p90 and 10-90% range."
    result = verify(valid_explanation, valid_bundle)
    assert result["status"] == "pass"

def test_duplicate_plan_id_fails(valid_explanation, valid_bundle):
    valid_explanation["plans_text"][2]["plan_id"] = "A"
    result = verify(valid_explanation, valid_bundle)
    assert result["status"] == "fail"
    assert any("Expected plan IDs ['A', 'B', 'C'] in order" in f for f in result["suitability_flags"])
