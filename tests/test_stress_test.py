"""
Tests for the single-shock-combination evaluator of §6 Stress Test.
"""

import sys
import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engines.stress_test import evaluate_combination  # noqa: E402


# ------------------------------------------------------------- test data

PLAN_B = {
    "plan_id": "B",
    "monthly_investment": 30000,
    "goal_amount": 2500000,
    "projected_corpus": 2410000,
}

PLAN_SURVIVE = {
    "plan_id": "S",
    "monthly_investment": 10000,
    "goal_amount": 2000000,
    "projected_corpus": 3000000,  # huge surplus
}

EVENT_APPRAISAL = {
    "event_id": "appraisal_miss",
    "label": "Appraisal comes in at 4% instead of 10%",
    "annual_probability": 0.23,
    "cash_impact": -180000,
}

EVENT_MEDICAL = {
    "event_id": "medical_expense",
    "label": "Family medical expense",
    "annual_probability": 0.10,
    "cash_impact": -200000,
}

EVENT_RENT = {
    "event_id": "rent_hike",
    "label": "Landlord raises rent by 15%",
    "annual_probability": 0.30,
    "cash_impact": -120000,
}


# ----------------------------------------------------------------- tests

def test_c001_plan_b_failing_combination():
    """Reproduce the contract's expected Plan B failure exactly."""
    events = [EVENT_APPRAISAL, EVENT_MEDICAL]
    res = evaluate_combination(PLAN_B, events)

    assert res["survives"] is False
    assert res["breaking_probability"] == 0.023
    assert res["shortfall_if_hit"] == 470000

    # Ensure events were copied directly
    combo = res["breaking_combo"]
    assert len(combo) == 2
    assert combo[0]["event_id"] == "appraisal_miss"
    assert combo[1]["event_id"] == "medical_expense"


def test_surviving_combination():
    """A combination that doesn't break the plan returns null/None for details."""
    events = [EVENT_APPRAISAL, EVENT_MEDICAL]
    res = evaluate_combination(PLAN_SURVIVE, events)

    assert res["survives"] is True
    assert res["breaking_combo"] is None
    assert res["breaking_probability"] is None
    assert res["shortfall_if_hit"] is None


def test_three_event_combination():
    """Evaluate exactly three events."""
    events = [EVENT_APPRAISAL, EVENT_MEDICAL, EVENT_RENT]
    res = evaluate_combination(PLAN_B, events)

    assert res["survives"] is False
    # 0.23 * 0.10 * 0.30 = 0.0069
    assert res["breaking_probability"] == 0.0069
    # Total impact = -180k + -200k + -120k = -500k
    # Effective corpus = 2410k - 500k = 1910k
    # Goal = 2500k, Shortfall = 2500k - 1910k = 590000
    assert res["shortfall_if_hit"] == 590000
    assert len(res["breaking_combo"]) == 3


def test_invalid_event_count_raises():
    """Only 2 or 3 events are allowed."""
    with pytest.raises(ValueError, match="exactly 2 or 3 events"):
        evaluate_combination(PLAN_B, [EVENT_APPRAISAL])

    with pytest.raises(ValueError, match="exactly 2 or 3 events"):
        evaluate_combination(PLAN_B, [EVENT_APPRAISAL] * 4)


def test_missing_event_field_raises():
    """Every event must have the required schema."""
    bad_event = dict(EVENT_APPRAISAL)
    del bad_event["cash_impact"]

    with pytest.raises(ValueError, match="missing required fields"):
        evaluate_combination(PLAN_B, [EVENT_MEDICAL, bad_event])


def test_deterministic_repeated_evaluation():
    """Same inputs produce exactly the same output."""
    events = [EVENT_APPRAISAL, EVENT_RENT]
    a = evaluate_combination(PLAN_B, events)
    b = evaluate_combination(PLAN_B, events)
    assert a == b


# ------------------------------------------------------------- search tests

from engines.stress_test import search_combinations  # noqa: E402

def test_search_three_events_count():
    """A three-event library evaluates exactly C(3,2) + C(3,3) = 3 + 1 = 4 combinations."""
    events = [EVENT_APPRAISAL, EVENT_MEDICAL, EVENT_RENT]
    res = search_combinations(PLAN_SURVIVE, events)
    assert res["combos_tested"] == 4


def test_search_ten_events_count():
    """A ten-event library evaluates exactly C(10,2) + C(10,3) = 45 + 120 = 165 combinations."""
    events = []
    for i in range(10):
        events.append({
            "event_id": f"event_{i}",
            "label": f"Test Event {i}",
            "annual_probability": 0.10,
            "cash_impact": -10000,
        })
    res = search_combinations(PLAN_SURVIVE, events)
    assert res["combos_tested"] == 165


def test_search_c001_plan_b_failing_combination():
    """Plan B fails with the cheapest combination."""
    events = [EVENT_APPRAISAL, EVENT_MEDICAL, EVENT_RENT]
    res = search_combinations(PLAN_B, events)

    assert res["survives"] is False
    assert res["combos_tested"] == 4

    # Cheapest combination should be Appraisal (-180k) and Rent Hike (-120k).
    # Total impact: -300k. 
    # Let's verify: 
    # Projected: 2410k, Goal: 2500k.
    # Impact needed to fail: anything < -90k.
    # Combinations:
    # A+M = -380k
    # A+R = -300k (Cheapest 2-event)
    # M+R = -320k
    # A+M+R = -500k
    # So A+R should be selected as the cheapest.
    
    combo = res["breaking_combo"]
    assert len(combo) == 2
    ids = {e["event_id"] for e in combo}
    assert ids == {"appraisal_miss", "rent_hike"}

    # Probability: 0.23 * 0.30 = 0.069
    assert res["breaking_probability"] == 0.069

    # Shortfall: 2500k - (2410k - 300k) = 2500k - 2110k = 390000
    assert res["shortfall_if_hit"] == 390000

    # Events copied exactly
    for ev in combo:
        assert set(ev.keys()) == {"event_id", "label", "annual_probability", "cash_impact"}


def test_search_plan_a_surviving():
    """Plan A survives all combinations if it has a large enough corpus."""
    plan_a = {
        "plan_id": "A",
        "monthly_investment": 35000,
        "goal_amount": 2500000,
        "projected_corpus": 3000000,
    }
    events = [EVENT_APPRAISAL, EVENT_MEDICAL, EVENT_RENT]
    res = search_combinations(plan_a, events)

    assert res["survives"] is True
    assert res["combos_tested"] == 4
    assert res["breaking_combo"] is None
    assert res["breaking_probability"] is None
    assert res["shortfall_if_hit"] is None


def test_search_deterministic():
    """Repeated execution must produce identical results."""
    events = [EVENT_APPRAISAL, EVENT_MEDICAL, EVENT_RENT]
    a = search_combinations(PLAN_B, events)
    b = search_combinations(PLAN_B, events)
    assert a == b


# ----------------------------------------------------------------- run()

from engines.stress_test import run  # noqa: E402

def test_run_c001_mock_plans():
    """Test the complete multi-plan execution using standard inputs."""
    # Plan A: survives. (2660000 projected corpus, but actually fails against 10-event library if impact > -160k!
    # Wait, 10 events: job_loss_3m = -360k.
    # Plan A survives if we give it a massive corpus, but here we should just pass the standard ones and see the result.
    # The requirement is to test the actual real Plan Generator output shape.
    plan_gen_output = {
        "assumptions_version": "assump-v1",
        "plans": [
            {
                "plan_id": "A",
                "monthly_investment": 35000,
                "goal_amount": 2500000,
                "projected_corpus": 2660000
            },
            {
                "plan_id": "B",
                "monthly_investment": 30000,
                "goal_amount": 2500000,
                "projected_corpus": 2410000
            },
            {
                "plan_id": "C",
                "monthly_investment": 52000,
                "goal_amount": 2500000,
                "projected_corpus": 4410000
            }
        ]
    }

    out = run(plan_gen_output)

    assert "results" in out
    results = out["results"]

    # 4. Three-plan execution & 5. Plan order preservation
    assert len(results) == 3
    assert results[0]["plan_id"] == "A"
    assert results[1]["plan_id"] == "B"
    assert results[2]["plan_id"] == "C"

    for r in results:
        # 1. Exact 165-combination count with the real 10-event library
        assert r["combos_tested"] == 165

    # Plan C should survive because it has a huge corpus (4410000 vs 2500000 = 1910000 buffer)
    # The maximum impact from 3 events out of 10 would be approx -360k -200k -180k = -740k
    # So 1910000 buffer is plenty. Plan C survives.
    # 7. Surviving-plan null fields
    rc = results[2]
    assert rc["survives"] is True
    assert rc["breaking_combo"] is None
    assert rc["breaking_probability"] is None
    assert rc["shortfall_if_hit"] is None

    # Plan B (buffer = -90k) fails immediately since it's already below goal.
    # The cheapest combination will just be the one with the smallest absolute impact.
    # The smallest negative impact in the 10 events is appliance_failure (-40000)
    # and car_repair (-50000). Total: -90000.
    rb = results[1]
    assert rb["survives"] is False
    assert rb["breaking_combo"] is not None
    # 11. Event-object preservation
    for ev in rb["breaking_combo"]:
        assert "event_id" in ev
        assert "annual_probability" in ev
        assert "cash_impact" in ev
        assert "label" in ev

    # 9. Probability-product correctness
    expected_prob = 1.0
    for ev in rb["breaking_combo"]:
        expected_prob *= ev["annual_probability"]
    assert rb["breaking_probability"] == round(expected_prob, 6)

    # 10. Shortfall correctness using the mathematical engine formula
    impact = sum(ev["cash_impact"] for ev in rb["breaking_combo"])
    # 2500000 - (2410000 + impact) = 90000 - impact
    assert rb["shortfall_if_hit"] == 2500000 - (2410000 + impact)

    # 6. Determinism
    out_second = run(plan_gen_output)
    assert out == out_second


def test_run_invalid_plan_missing_fields_raises():
    """12. Invalid plan input validation."""
    bad_output = {
        "plans": [
            {
                "plan_id": "X"
                # Missing projected_corpus, goal_amount
            }
        ]
    }
    with pytest.raises(KeyError):
        run(bad_output)

