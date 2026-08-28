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

