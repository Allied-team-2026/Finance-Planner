"""
§6 Stress Test - combination evaluator.

Evaluates single combinations of shock events. The full engine (combination
search and multi-plan evaluation) will be added in a later step.
"""

def evaluate_combination(plan, events):
    """Evaluate whether a plan survives a specific combination of shock events.

    Args:
        plan: dict with at least 'projected_corpus' and 'goal_amount'.
        events: list of exactly 2 or 3 event dicts from the shock library.

    Returns:
        dict with fields needed to construct a single combination result:
        - survives
        - breaking_combo
        - breaking_probability
        - shortfall_if_hit
    """
    if len(events) not in (2, 3):
        raise ValueError(f"Stress combinations must have exactly 2 or 3 events, got {len(events)}.")

    required_keys = {"event_id", "label", "annual_probability", "cash_impact"}
    total_impact = 0
    prob = 1.0

    for ev in events:
        if not required_keys.issubset(ev.keys()):
            raise ValueError(f"Event missing required fields: {ev}")
        total_impact += ev["cash_impact"]
        prob *= ev["annual_probability"]

    effective_corpus = plan["projected_corpus"] + total_impact
    goal = plan["goal_amount"]

    survives = effective_corpus >= goal

    if survives:
        return {
            "survives": True,
            "breaking_combo": None,
            "breaking_probability": None,
            "shortfall_if_hit": None,
        }
    else:
        return {
            "survives": False,
            "breaking_combo": [dict(ev) for ev in events],
            "breaking_probability": round(prob, 6),
            "shortfall_if_hit": goal - effective_corpus,
        }


import itertools

def search_combinations(plan, events):
    """Enumerate all 2-event and 3-event combinations to find the cheapest failure.

    'Cheapest' is defined as the combination that causes failure with the smallest
    absolute cash impact (i.e. the highest/least-negative total impact).

    Args:
        plan: the Plan Generator output plan object.
        events: the complete list of shock events from the library.

    Returns:
        dict with survives, breaking_combo, breaking_probability,
        shortfall_if_hit, and combos_tested.
    """
    combos_tested = 0
    failing_results = []

    # Evaluate 2-event combinations
    for combo in itertools.combinations(events, 2):
        combos_tested += 1
        res = evaluate_combination(plan, list(combo))
        if not res["survives"]:
            failing_results.append(res)

    # Evaluate 3-event combinations
    for combo in itertools.combinations(events, 3):
        combos_tested += 1
        res = evaluate_combination(plan, list(combo))
        if not res["survives"]:
            failing_results.append(res)

    if failing_results:
        # Sort by total cash impact descending (closest to zero / least negative)
        # to find the "cheapest" combination that breaks the plan.
        failing_results.sort(
            key=lambda r: sum(e["cash_impact"] for e in r["breaking_combo"]),
            reverse=True
        )
        cheapest = failing_results[0]
        cheapest["combos_tested"] = combos_tested
        return cheapest
    else:
        return {
            "survives": True,
            "breaking_combo": None,
            "breaking_probability": None,
            "shortfall_if_hit": None,
            "combos_tested": combos_tested,
        }

import json
from pathlib import Path

# Module-level constant for the event library path
SHOCKS_PATH = Path(__file__).resolve().parent.parent / "data" / "shock_events.json"


def load_events():
    """Load the complete shock event library."""
    with open(SHOCKS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def run(plan_generator_output):
    """
    Public API for the Stress Test engine.

    Args:
        plan_generator_output: The complete JSON output from the Plan Generator,
                               containing a list of plans under the "plans" key.
    
    Returns:
        dict: A "results" object mapping the stress test outcome per plan_id.
    """
    events = load_events()
    
    # We must support exactly 165 combinations if it's the 10-event library
    # The helper `search_combinations` already handles combinations natively.
    
    results = []
    plans = plan_generator_output.get("plans", [])
    
    for plan in plans:
        # evaluate the combinations
        combo_res = search_combinations(plan, events)
        
        # build the required structure for this plan
        res_obj = {
            "plan_id": plan["plan_id"],
            "survives": combo_res["survives"],
            "breaking_combo": combo_res["breaking_combo"],
            "breaking_probability": combo_res["breaking_probability"],
            "shortfall_if_hit": combo_res["shortfall_if_hit"],
            "combos_tested": combo_res["combos_tested"]
        }
        
        results.append(res_obj)
        
    return {
        "results": results
    }


