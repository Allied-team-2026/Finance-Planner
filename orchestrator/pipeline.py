"""
The pipeline.

Every stage is either a real engine or that stage's mock file, and switching one
for the other is a one-line change: add the stage name to REAL_ENGINES. So the
whole pipeline returns a complete, correct response today, before a single engine
exists, and it keeps working as each engine lands one at a time.

Nothing in this file computes a number. Engines compute; this file moves data
between them, drops the identifying fields before any agent sees anything, and
puts the name back afterwards.
"""

from datetime import datetime, timezone
from importlib import import_module
from pathlib import Path
import json

MOCKS = Path(__file__).resolve().parent.parent / "mocks"
SCHEMA_VERSION = "api-v1"

# Add a stage name here once its engine passes its own test. Anything not listed
# runs on its mock. Keep this list honest - a stage listed here that returns
# rubbish is worse than a mock, because the response still looks complete.
REAL_ENGINES = set()

# stage name -> (mock file, "module:function" for the real engine)
STAGES = {
    "customer":    ("customer_C001.json",   "engines.synthetic_data:load_customer"),
    "profile":     ("profile_out.json",     "engines.profile:build_profile"),
    "features":    ("features_out.json",    "engines.features:extract"),
    "risk":        ("risk_out.json",        "models.risk_model:predict"),
    "plans":       ("plans_out.json",       "engines.plan_generator:generate"),
    "montecarlo":  ("montecarlo_out.json",  "engines.montecarlo:simulate"),
    "stress":      ("stress_out.json",      "engines.stress_test:run"),
    "cohort":      ("peer_cohort_out.json", "engines.peer_cohort:summarise"),
    "explanation": ("explanation_out.json", "agents.explanation:explain"),
    "challenge":   ("challenge_out.json",   "agents.challenger:challenge"),
    "verify":      ("verifier_out.json",    "engines.verifier:verify"),
}


def load_mock(filename):
    """Read a mock, dropping the _mock_note used to document it."""
    with open(MOCKS / filename) as f:
        return {k: v for k, v in json.load(f).items() if not k.startswith("_")}


def run(stage, *args):
    """Run one stage. Mocks ignore their arguments, which is the point."""
    mock_file, target = STAGES[stage]
    if stage not in REAL_ENGINES:
        return load_mock(mock_file)
    module_name, function_name = target.split(":")
    return getattr(import_module(module_name), function_name)(*args)


def engine_status():
    """Which stages are real yet. Useful for standups and the trust panel."""
    return {name: ("engine" if name in REAL_ENGINES else "mock") for name in STAGES}


# --------------------------------------------------------------- section 7

def merge_plans(plans, montecarlo, stress, keep_return):
    """Join the three per-plan sources on plan_id.

    Two field names are deliberately renamed exactly once, here: the stress
    engine returns `survives` and everything downstream reads `survives_stress`.
    Do not "fix" this at either end.
    """
    by_sim = {r["plan_id"]: r for r in montecarlo["results"]}
    by_stress = {r["plan_id"]: r for r in stress["results"]}

    merged = []
    for plan in plans["plans"]:
        sim, st = by_sim[plan["plan_id"]], by_stress[plan["plan_id"]]
        row = {k: v for k, v in plan.items()
               if keep_return or k != "expected_annual_return"}
        row.update({k: v for k, v in sim.items() if k != "plan_id"})
        row.update({
            "survives_stress": st["survives"],
            "breaking_combo": st["breaking_combo"],
            "breaking_probability": st["breaking_probability"],
            "shortfall_if_hit": st["shortfall_if_hit"],
        })
        merged.append(row)
    return merged


def compare(plans):
    """Cross-plan numbers, precomputed because no agent may do arithmetic."""
    cheapest = min(plans, key=lambda p: p["monthly_investment"])
    return {
        "cheapest_plan_id": cheapest["plan_id"],
        "highest_success_plan_id": max(plans, key=lambda p: p["success_probability"])["plan_id"],
        "plan_count": len(plans),
        "monthly_investment_delta_vs_cheapest": {
            p["plan_id"]: p["monthly_investment"] - cheapest["monthly_investment"]
            for p in plans
        },
    }


def build_bundle(customer, profile, features, risk, plans, montecarlo, stress):
    """Section 7. The only payload any agent ever sees.

    Identifiers are dropped here and nowhere else, so there is exactly one place
    to check that no name and no customer_id can reach an LLM. Age, dependents,
    employment and city tier stay, because they describe rather than identify and
    the agent cannot write anything contextual without them.
    """
    merged = merge_plans(plans, montecarlo, stress, keep_return=False)
    return {
        "context": {k: customer[k] for k in
                    ("age", "dependents", "employment_type", "city_tier")},
        "profile": {k: profile[k] for k in
                    ("net_worth", "monthly_income", "monthly_expense",
                     "monthly_surplus", "emergency_fund_months",
                     "risk_capacity", "risk_capacity_reasons")},
        "risk": {
            "stated": risk["stated_risk"],
            "revealed": risk["revealed_risk"],
            "confidence": risk["confidence"],
            "mismatch": risk["mismatch"],
            "panic_sell_count": features["panic_sell_count"],
            "evidence": risk["evidence"],
        },
        "goals": customer["goals"],
        "plans": merged,
        "comparisons": compare(merged),
        "n_simulations": montecarlo["n_simulations"],
    }


# -------------------------------------------------------------- section 11

def build_response(customer, profile, risk, plans, montecarlo, stress,
                   explanation, cohort, verifier, challenge=None):
    """Section 11. What the API returns and the UI renders.

    Wider than the agent payload on purpose: the name comes back, and the plans
    carry the fields a screen needs but an agent has no business seeing.
    """
    text = {p["plan_id"]: p for p in explanation["plans_text"]}
    merged = merge_plans(plans, montecarlo, stress, keep_return=True)
    for plan in merged:
        plan.update({k: text[plan["plan_id"]][k]
                     for k in ("headline", "body", "pros", "cons")})

    return {
        "schema_version": SCHEMA_VERSION,
        "customer_id": customer["customer_id"],
        "customer_name": customer["name"],
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "context": {k: customer[k] for k in
                    ("age", "dependents", "employment_type", "city_tier")},
        "profile": profile,
        "risk": {
            "stated": risk["stated_risk"],
            "revealed": risk["revealed_risk"],
            "confidence": risk["confidence"],
            "mismatch": risk["mismatch"],
            "features_used": risk["features_used"],
            "evidence": risk["evidence"],
            "model_version": risk["model_version"],
        },
        "goals": customer["goals"],
        "plans": merged,
        "goal_priority_note": explanation["goal_priority_note"],
        "mismatch_note": explanation["mismatch_note"],
        "peer_cohort": cohort,
        "challenge": challenge,
        "verifier": verifier,
        "meta": {
            "returns_data_source": montecarlo["returns_data_source"],
            "n_simulations": montecarlo["n_simulations"],
            "assumptions_version": plans["assumptions_version"],
            "model_version": risk["model_version"],
        },
    }


# ------------------------------------------------------------- the pipeline

def run_engines(customer_id, extra_monthly_savings=0):
    """Every engine stage in dependency order, plus the §7 bundle they feed.

    The wiring lives here and nowhere else. Which stage takes which arguments is
    exactly the thing that breaks when a mock is swapped for a real engine, so
    anything that wants to run the pipeline - production paths and tests alike -
    calls this rather than repeating the order. A test that wires the pipeline
    itself can pass against wiring production does not use.

    A what-if is the same pipeline with more surplus to work with. Applying it to
    the surplus here - not inside the plan generator - means §4's signature never
    has to know what-ifs exist.
    """
    customer = run("customer", customer_id)
    profile = run("profile", customer)

    # §3a takes the profile as well as the customer, because
    # `emergency_fund_months` is §2's number and recomputing it here would put a
    # second copy of §2's formula in a second file.
    #
    # It runs before the what-if is applied, and must keep running before it.
    # Revealed risk describes what this customer has already done with their
    # money, so a hypothetical extra 5,000 a month must not be able to move the
    # risk prediction. Today no feature reads the surplus, so the order does not
    # change any number - it stops the day someone adds one.
    features = run("features", customer, profile)
    risk = run("risk", features)

    if extra_monthly_savings:
        profile = dict(profile)
        profile["monthly_surplus"] += extra_monthly_savings

    plans = run("plans", profile, risk)
    montecarlo = run("montecarlo", plans)
    stress = run("stress", plans, profile)
    cohort = run("cohort", customer, profile)

    return {
        "customer": customer, "profile": profile, "features": features,
        "risk": risk, "plans": plans, "montecarlo": montecarlo,
        "stress": stress, "cohort": cohort,
        "bundle": build_bundle(customer, profile, features, risk,
                               plans, montecarlo, stress),
    }


def run_stages(customer_id, extra_monthly_savings=0):
    """run_engines plus the agent stages, which read only the bundle.

    Split from run_engines because the challenge path needs the bundle and must
    not pay for an explanation and a verification it will not use - two LLM calls
    on a live demo.
    """
    s = run_engines(customer_id, extra_monthly_savings)
    s["explanation"] = run("explanation", s["bundle"])
    s["verify"] = run("verify", s["explanation"], s["bundle"])
    return s


def make_plan(customer_id, extra_monthly_savings=0):
    """The whole thing. Returns what the API serves and the UI renders."""
    s = run_stages(customer_id, extra_monthly_savings)
    return build_response(s["customer"], s["profile"], s["risk"], s["plans"],
                          s["montecarlo"], s["stress"], s["explanation"],
                          s["cohort"], s["verify"])


def make_challenge(customer_id, chosen_plan_id):
    """Runs only after the customer picks a plan."""
    bundle = run_engines(customer_id)["bundle"]
    return run("challenge", bundle, chosen_plan_id)
