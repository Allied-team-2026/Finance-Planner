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
                "success_probability": 0.73,
                "shortfall_if_hit": 5000
            },
            {
                "plan_id": "B",
                "monthly_investment": 30000,
                "allocation": {"equity": 0.65, "debt": 0.35},
                "projected_corpus": 2410000,
                "success_probability": 0.56,
                "shortfall_if_hit": 15000
            },
            {
                "plan_id": "C",
                "monthly_investment": 52000,
                "allocation": {"equity": 0.85, "debt": 0.15},
                "projected_corpus": 4410000,
                "success_probability": 0.92,
                "shortfall_if_hit": 7000
            }
        ],
        "goals": [],
        "comparisons": {
            "monthly_investment_delta_vs_cheapest": {"A": 2222}
        },
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
                "body": "Invest 35000 for 2,660,000. 40% equity. 73% success. Shortfall 5000.",
                "pros": [],
                "cons": []
            },
            {
                "plan_id": "B",
                "headline": "Plan B",
                "body": "Invest 30,000 for 2410000. 65% equity. 56% success. Shortfall 15000.",
                "pros": [],
                "cons": []
            },
            {
                "plan_id": "C",
                "headline": "Plan C",
                "body": "Invest 52,000 for 4410000. 85% equity. 92% success. Shortfall 7000.",
                "pros": [],
                "cons": []
            }
        ],
        "goal_priority_note": "note",
        "mismatch_note": "stated aggressive but revealed moderate.",
        "peer_cohort_note": "cohort of 20 with 0.37 savings.",
        "numbers_used": [35000, 2660000, 0.40, 0.73, 5000, 30000, 2410000, 0.65, 0.56, 15000, 52000, 4410000, 0.85, 0.92, 7000, 20, 0.37]
    }

def test_valid_explanation_passes(valid_explanation, valid_bundle):
    result = verify(valid_explanation, valid_bundle)
    assert result["status"] == "pass"

def test_valid_plan_comparison_passes(valid_explanation, valid_bundle):
    # Plan A vs Plan B comparison explicitly naming both plans
    valid_explanation["plans_text"][0]["body"] += " Plan A costs 2222 more than Plan B."
    valid_explanation["numbers_used"].append(2222)
    result = verify(valid_explanation, valid_bundle)
    assert result["status"] == "pass"

def test_comparison_number_not_present_fails(valid_explanation, valid_bundle):
    # "comparison number not present in comparison fields"
    valid_explanation["plans_text"][0]["body"] += " Plan A costs 5555 more than Plan B."
    result = verify(valid_explanation, valid_bundle)
    assert result["status"] == "fail"
    assert any("5555" in str(u) for u in result["unverified_numbers"])

def test_p10_p90_labels_pass(valid_explanation, valid_bundle):
    valid_explanation["plans_text"][0]["body"] += " 10th percentile and p90 and 10-90% range."
    result = verify(valid_explanation, valid_bundle)
    assert result["status"] == "pass"

def test_valid_risk_evidence_numbers_pass(valid_explanation, valid_bundle):
    # Already included in valid_explanation through 0.37 etc
    assert verify(valid_explanation, valid_bundle)["status"] == "pass"

def test_valid_cohort_numbers_pass(valid_explanation, valid_bundle):
    # 20 and 0.37 are tested
    assert verify(valid_explanation, valid_bundle)["status"] == "pass"

def test_cross_plan_contamination_investment_fails(valid_explanation, valid_bundle):
    # Plan A uses Plan B monthly investment
    valid_explanation["plans_text"][0]["body"] += " Invest 30000."
    result = verify(valid_explanation, valid_bundle)
    assert result["status"] == "fail"
    assert any("Cross-plan contamination" in f for f in result["suitability_flags"])

def test_cross_plan_contamination_corpus_fails(valid_explanation, valid_bundle):
    # Plan B uses Plan C corpus
    valid_explanation["plans_text"][1]["body"] += " Corpus 4410000."
    result = verify(valid_explanation, valid_bundle)
    assert result["status"] == "fail"
    assert any("Cross-plan contamination" in f for f in result["suitability_flags"])

def test_cross_plan_contamination_success_probability_fails(valid_explanation, valid_bundle):
    # Plan C uses Plan A success probability
    valid_explanation["plans_text"][2]["body"] += " Success 73%."
    result = verify(valid_explanation, valid_bundle)
    assert result["status"] == "fail"
    assert any("Cross-plan contamination" in f for f in result["suitability_flags"])

def test_cross_plan_contamination_allocation_fails(valid_explanation, valid_bundle):
    # Plan A claims another plan's allocation
    valid_explanation["plans_text"][0]["body"] += " 65% equity."
    result = verify(valid_explanation, valid_bundle)
    assert result["status"] == "fail"
    assert any("Cross-plan contamination" in f for f in result["suitability_flags"])

def test_cross_plan_contamination_shortfall_fails(valid_explanation, valid_bundle):
    # wrong stress shortfall assigned to another plan
    valid_explanation["plans_text"][0]["body"] += " Shortfall 15000."
    result = verify(valid_explanation, valid_bundle)
    assert result["status"] == "fail"
    assert any("Cross-plan contamination" in f for f in result["suitability_flags"])

def test_fabricated_number_fails(valid_explanation, valid_bundle):
    valid_explanation["plans_text"][0]["body"] += " 99999"
    result = verify(valid_explanation, valid_bundle)
    assert result["status"] == "fail"
    assert any("99999" in str(u) for u in result["unverified_numbers"])

def test_privacy_violation_fails(valid_explanation, valid_bundle):
    valid_explanation["mismatch_note"] = "C001 is the customer."
    result = verify(valid_explanation, valid_bundle)
    assert result["status"] == "fail"
    assert any("Privacy violation" in f for f in result["suitability_flags"])

def test_forbidden_categorical_claim_fails(valid_explanation, valid_bundle):
    valid_explanation["plans_text"][0]["body"] += " I guarantee this will work."
    result = verify(valid_explanation, valid_bundle)
    assert result["status"] == "fail"
    assert any("Forbidden claim" in f for f in result["suitability_flags"])
