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
