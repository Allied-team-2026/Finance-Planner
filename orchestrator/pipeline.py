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
import math
import groq

from agents.numeric import extract_numbers_with_paths

MOCKS = Path(__file__).resolve().parent.parent / "mocks"
SCHEMA_VERSION = "api-v1"

# Add a stage name here once its engine passes its own test. Anything not listed
# runs on its mock. Keep this list honest - a stage listed here that returns
# rubbish is worse than a mock, because the response still looks complete.
PRODUCTION_ENGINES = {
    "customer",
    "profile",
    "features",
    "risk",
    "plans",
    "montecarlo",
    "stress",
    "cohort",
    "explanation",
    "challenge",
    "verify",
}
REAL_ENGINES = PRODUCTION_ENGINES.copy()

# stage name -> (mock file, "module:function" for the real engine)
STAGES = {
    "customer":    ("customer_C001.json",   "engines.synthetic_data:load_customer"),
    "profile":     ("profile_out.json",     "engines.profile:build_profile"),
    "features":    ("features_out.json",    "engines.features:extract"),
    "risk":        ("risk_out.json",        "models.risk_model:predict"),
    "plans":       ("plans_out.json",       "engines.plan_generator:generate"),
    "montecarlo":  ("montecarlo_out.json",  "engines.montecarlo:simulate"),
    "stress":      ("stress_out.json",      "engines.stress_test:run"),
    "cohort":      ("peer_cohort_out.json", "engines.peer_cohort:run"),
    "explanation": ("explanation_out.json", "agents.explanation:explain"),
    "challenge":   ("challenge_out.json",   "agents.challenger:challenge"),
    "verify":      ("verifier_out.json",    "agents.verifier:verify"),
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
            "combos_tested": st["combos_tested"],
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


def build_bundle(customer, profile, features, risk, plans, montecarlo, stress, cohort):
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
        "peer_cohort": cohort,
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
    risk = run("risk", features, customer["stated_risk"])

    if extra_monthly_savings:
        profile = dict(profile)
        profile["monthly_surplus"] += extra_monthly_savings

    plans = run("plans", profile, risk, customer.get("goals", []))
    montecarlo = run("montecarlo", plans)
    stress = run("stress", plans)
    
    from engines.synthetic_data import generate_dataset
    customers = generate_dataset(1000, seed=42)
    cohort = run("cohort", customers, customer, profile, risk)

    return {
        "customer": customer, "profile": profile, "features": features,
        "risk": risk, "plans": plans, "montecarlo": montecarlo,
        "stress": stress, "cohort": cohort,
        "bundle": build_bundle(customer, profile, features, risk,
                               plans, montecarlo, stress, cohort),
    }


def get_customer_profile(customer_id):
    """Lightweight retrieval of a customer's basic demographics and financial profile.
    
    This function runs only the absolute minimum required stages to derive net worth 
    and expenses, completely bypassing LLMs, Monte Carlo, and Challenger logic.
    It intentionally scrubs sensitive raw transactions and model parameters.
    """
    try:
        customer = run("customer", customer_id)
    except FileNotFoundError:
        raise ValueError(f"Customer {customer_id} not found")

    profile = run("profile", customer)
    
    return {
        "customer_id": customer.get("customer_id", customer_id),
        "customer_name": customer["name"],
        "age": customer.get("age"),
        "dependents": customer.get("dependents", 0),
        "employment_type": customer.get("employment_type"),
        "city_tier": customer.get("city_tier"),
        "monthly_income": profile.get("monthly_income"),
        "monthly_expense": profile.get("monthly_expense"),
        "monthly_surplus": profile.get("monthly_surplus"),
        "net_worth": profile.get("net_worth"),
        "emergency_fund_months": profile.get("emergency_fund_months"),
        "stated_risk": customer.get("stated_risk"),
        "goals": customer.get("goals", [])
    }


def run_stages(customer_id, extra_monthly_savings=0):
    """run_engines plus the agent stages, which read only the bundle.

    Split from run_engines because the challenge path needs the bundle and must
    not pay for an explanation and a verification it will not use - two LLM calls
    on a live demo.
    """
    s = run_engines(customer_id, extra_monthly_savings)
    
    max_attempts = 3
    previous_failures = None
    
    for attempt in range(max_attempts):
        try:
            if previous_failures:
                s["explanation"] = run("explanation", s["bundle"], previous_failures)
            else:
                s["explanation"] = run("explanation", s["bundle"])
        except (groq.GroqError, ValueError) as e:
            previous_failures = [f"API Generation Error: {str(e)}"]
            continue
            
        s["verify"] = run("verify", s["explanation"], s["bundle"])
        
        if s["verify"]["status"] == "pass":
            break
            
        # Collect failures for next attempt
        previous_failures = s["verify"].get("unverified_numbers", []) + s["verify"].get("suitability_flags", [])
        if not previous_failures:
            previous_failures = ["The previous response failed structural or numeric verification."]
    else:
        from agents.explanation import fallback_explain
        s["explanation"] = fallback_explain(s["bundle"])
        s["verify"] = run("verify", s["explanation"], s["bundle"])
        
    return s


def make_plan(customer_id, extra_monthly_savings=0):
    """The whole thing. Returns what the API serves and the UI renders."""
    s = run_stages(customer_id, extra_monthly_savings)
    return build_response(s["customer"], s["profile"], s["risk"], s["plans"],
                          s["montecarlo"], s["stress"], s["explanation"],
                          s["cohort"], s["verify"])


def run_challenge_with_retries(s, chosen_plan_id, max_attempts=3):
    """The challenge, retried on its own refusals, then templated if it must be.

    The challenge agent refuses its own output when a number is not in the bundle
    or a privacy rule is broken, and that refusal is a ValueError. With one attempt
    and no fallback it reached the API as a 500 and the challenge panel simply
    stayed empty - which is what "challenge does nothing for plan A" was. The
    explanation stage has had a retry and a template fallback all along; this
    gives the challenge the same two.

    A mock ignores its arguments, so retrying it would return the same canned
    answer three times. Mocked stages get one attempt and the guards in
    make_challenge still catch them.
    """
    if "challenge" not in REAL_ENGINES:
        return run("challenge", s["bundle"], s["explanation"], s["verify"],
                   chosen_plan_id)

    from agents.challenger import challenge as challenge_agent, fallback_challenge

    failures = None
    for _ in range(max_attempts):
        try:
            return challenge_agent(s["bundle"], s["explanation"], s["verify"],
                                   chosen_plan_id, failures)
        except (groq.GroqError, ValueError) as e:
            failures = [str(e)]

    return fallback_challenge(s["bundle"], chosen_plan_id)


def make_challenge(customer_id, chosen_plan_id):
    """Runs only after the customer picks a plan."""
    s = run_stages(customer_id)
    
    # validate chosen_plan_id
    if not any(p["plan_id"] == chosen_plan_id for p in s["plans"]["plans"]):
        raise ValueError(f"Invalid chosen_plan_id: {chosen_plan_id}")
        
    challenge = run_challenge_with_retries(s, chosen_plan_id)

    # A mock ignores its arguments, so a challenge stage running on its mock hands
    # back the same canned plan every time - the caller asks about B and gets an
    # argument against C. That has to be loud: the screen cannot tell a wrong-plan
    # challenge from a right one, and a plausible argument about the wrong plan is
    # worse than no argument at all.
    returned = challenge.get("chosen_plan_id")
    if returned != chosen_plan_id:
        raise ValueError(
            f"challenge stage answered about plan {returned} when asked about "
            f"{chosen_plan_id}. The stage is running on its mock - check that "
            f"'challenge' is in PRODUCTION_ENGINES and restart the server."
        )

    # The plan-id check above misses the worse case. Asked about plan C, the mock
    # returns plan C, the ids agree, and C001's 52,000 lands on C003's screen with
    # nothing to show it is the wrong customer's money. So the numbers have to
    # belong to this customer's bundle. The challenge agent checks this on its own
    # output, but that check does not run when the stage is a mock - and a mock is
    # exactly when the numbers come from someone else.
    allowed = extract_numbers_with_paths(s["bundle"])
    for num in challenge.get("numbers_used", []):
        if not any(math.isclose(float(num), a, rel_tol=1e-5, abs_tol=1e-5)
                   for a in allowed):
            raise ValueError(
                f"challenge cites {num}, which is not in this customer's numbers. "
                f"The stage is running on its mock, so it is quoting another "
                f"customer - check that 'challenge' is in PRODUCTION_ENGINES and "
                f"restart the server."
            )

    # The screen shows one Auditor badge, driven by `verifier.status`. Until now
    # that badge reported on the explanation only, so it read "Pass" beside a
    # challenge nobody had checked. Folding the challenge result into the same
    # four fields keeps the badge's meaning - everything on this page was checked
    # - without the UI having to learn about a second verdict.
    #
    # Called directly rather than through run(): a stage exists so a mock can
    # stand in for an engine that is not written yet, and this engine is written.
    from agents.verifier import verify_challenge
    cv = verify_challenge(challenge, s["bundle"])
    combined = {
        "status": "fail" if "fail" in (s["verify"]["status"], cv["status"]) else "pass",
        "numbers_checked": s["verify"]["numbers_checked"] + cv["numbers_checked"],
        "unverified_numbers": s["verify"]["unverified_numbers"] + cv["unverified_numbers"],
        "suitability_flags": s["verify"]["suitability_flags"] + cv["suitability_flags"],
    }

    return build_response(s["customer"], s["profile"], s["risk"], s["plans"],
                          s["montecarlo"], s["stress"], s["explanation"],
                          s["cohort"], combined, challenge=challenge)
