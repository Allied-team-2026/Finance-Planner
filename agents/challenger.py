import json
import re

# A peer in the cohort data is named P1, P2, P42. A percentile label is p10, p25,
# p50, p75 or p90 - those name numbers the bundle hands over on purpose, so they
# are not identities and must be allowed through. Kept as one constant so the test
# checks the pattern production uses rather than its own copy of it.
PEER_ID_PATTERN = r'\bp(?!(?:10|25|50|75|90)\b)\d+\b'


def build_challenger_payload(bundle, explanation, verification):
    """
    Transforms the internal bundle, explanation, and verification results into
    the exact trimmed structure required by the Challenger Agent.
    """
    payload = {
        "context": bundle.get("context", {}),
        "profile": bundle.get("profile", {}),
        "risk": bundle.get("risk", {}),
        "goals": bundle.get("goals", []),
        "plans": bundle.get("plans", []),
        "comparisons": bundle.get("comparisons", {}),
        "n_simulations": bundle.get("n_simulations"),
        "peer_cohort": bundle.get("peer_cohort"),
        "explanation": explanation,
        "verification": verification
    }
        
    forbidden_keys = {
        "customer_id", "name", "customer_name", "account_numbers", 
        "transactions", "investment_events", "individual_peers", 
        "ground_truth_risk"
    }
    
    def clean(obj):
        if isinstance(obj, dict):
            return {k: clean(v) for k, v in obj.items() if k not in forbidden_keys}
        elif isinstance(obj, list):
            return [clean(v) for v in obj]
        return obj

    return clean(payload)

import os
import re
import math
import json

from agents.numeric import extract_numbers_with_paths, validate_prose_numbers

def challenge(bundle, explanation, verification, chosen_plan_id, previous_failures=None):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set")
        
    try:
        from groq import Groq
    except ImportError:
        raise ImportError("groq package is required. Run 'pip install groq'")
        
    payload = build_challenger_payload(bundle, explanation, verification)

    # The screen turns alternative_suggested into a "switch to this plan" button by
    # matching it against a real plan id. So the agent is only allowed to answer
    # with a plan id or "none". Free prose here would silently lose the answer.
    plan_ids = [p["plan_id"] for p in payload.get("plans", []) if p.get("plan_id")]
    allowed_alternatives = plan_ids + ["none"]
    
    # 1. Provide Verifier Status Context
    verification_context = "The Explanation has PASSED verification."
    if verification.get("status") == "fail":
        verification_context = "The Explanation FAILED verification. Do not blindly trust its assertions."

    system_prompt = f"""You are a financial challenger agent.
Your primary role is to identify weaknesses, expose trade-offs, question suitability, and point out limitations in the chosen plan.
Do NOT act as a second recommendation engine. 
Do NOT invent probabilities, new facts, or calculate/recalculate any financial figures.

CONTEXT:
{verification_context}
The authoritative bundle is the source of truth. Explanation is NOT authoritative.
Every factual/numeric claim you make must be supported by bundle data.

INSTRUCTIONS:
1. You MUST primarily challenge ONLY the specified chosen plan: {chosen_plan_id}.
2. Other plans may be referenced ONLY when an explicit comparison is useful. Do NOT generate separate challenges for other plans.
3. Treat `evidence_cited` as evidence references that must be traceable to the authoritative bundle data. 
4. Clearly distinguish between fact (from the bundle) and interpretation (your challenge).
5. Never identify the customer, account numbers, transactions, or individual peers. Do not reveal ground_truth_risk.
6. Use ONLY numbers present in the payload. Do not invent arbitrary numbers. Numbers must come from the engine sections - context, profile, risk, goals, plans, comparisons, n_simulations, peer_cohort. The "explanation" and "verification" blocks are there so you can question them, not to quote numbers from: a number that appears only in the explanation's prose will be rejected.
7. "alternative_suggested" must be exactly one plan id from {plan_ids}, or "none" if no other plan is better. No sentence, no explanation, no "Plan A" - just the letter.
8. Write every number with the same digits the payload uses. Never convert a number into lakh, crore, million or thousand, and never write it as a decimal multiple: 1350000 stays 1350000 and must not become "1.35 million" or "13.5 lakh". Converting units is arithmetic, and a converted number will be rejected.

FORMAT:
Output valid JSON matching the exact schema provided.
"""

    # A refused attempt is worth more to the model than a second identical try.
    # The checks below reject on exactly one reason at a time, so handing that
    # reason back is enough to steer it - this is how the explanation agent
    # already recovers, and the challenge had no equivalent.
    if previous_failures:
        system_prompt += (
            "\nYOUR PREVIOUS ATTEMPT WAS REJECTED FOR THIS REASON:\n"
            + "\n".join(f"- {f}" for f in previous_failures)
            + "\nFix exactly that and keep everything else the same.\n"
        )

    model_name = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
    
    schema = {
        "type": "object",
        "properties": {
            "chosen_plan_id": {"type": "string"},
            "challenge": {"type": "string"},
            "evidence_cited": {"type": "array", "items": {"type": "string"}},
            "alternative_suggested": {"type": "string", "enum": allowed_alternatives},
            "numbers_used": {"type": "array", "items": {"type": "number"}}
        },
        "required": ["chosen_plan_id", "challenge", "evidence_cited", "alternative_suggested", "numbers_used"],
        "additionalProperties": False
    }

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(payload)}
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "challenger_response",
                "strict": True,
                "schema": schema
            }
        },
        temperature=0.0,
        max_tokens=4000
    )
    
    result = json.loads(response.choices[0].message.content)
    
    # 1. Validate chosen_plan_id matching
    if result.get("chosen_plan_id") != chosen_plan_id:
        raise ValueError(f"returned chosen_plan_id '{result.get('chosen_plan_id')}' does not match input '{chosen_plan_id}'")
        
    # 2. Structure Validation
    for f in ["challenge", "alternative_suggested"]:
        if f not in result or not isinstance(result[f], str):
            raise ValueError(f"Missing or invalid '{f}'")
    if "evidence_cited" not in result or not isinstance(result["evidence_cited"], list):
        raise ValueError("Missing or invalid 'evidence_cited'")
    if "numbers_used" not in result or not isinstance(result["numbers_used"], list):
        raise ValueError("Missing or invalid 'numbers_used'")
    if result["alternative_suggested"] not in allowed_alternatives:
        raise ValueError(
            f"alternative_suggested '{result['alternative_suggested']}' is not a plan id or 'none'"
        )
        
    # 3. Privacy Validation
    result_str = json.dumps(result).lower()
    forbidden_terms = ["jane", "c001", "g00", "ground_truth_risk", "rahul", "mehta", "account", "transaction", "investment_event"]
    # Individual peers are named P1, P2 and must never be quoted. But p10, p50 and
    # p90 are percentile labels for numbers the bundle hands over on purpose -
    # p10_corpus, p90_corpus, p10_gap_to_goal - and the plan with the worst
    # downside is exactly the one worth challenging. A plain \bp\d+\b regex read
    # "the p10 outcome" as a peer ID and refused the whole challenge, which is why
    # challenging plan A returned nothing at all. The verifier already treats these
    # five as labels; this now agrees with it.
    if re.search(PEER_ID_PATTERN, result_str):
        raise ValueError("Privacy violation: individual peer ID found")
        
    for term in forbidden_terms:
        if term in result_str:
            raise ValueError(f"Privacy violation: '{term}' found in output")
            
    # 4. Numeric Validation
    #
    # The whitelist is the engines' numbers only. `payload` also carries the
    # explanation and the verification result, and extracting numbers from those
    # two lets a number launder itself into the challenge: the explanation's prose
    # said "a 40/60 equity-debt split", so 40 became legal here, and
    # verification.unverified_numbers made every number the verifier had just
    # refused legal too. The prompt says the explanation is not authoritative, so
    # its prose cannot be a source of truth for numbers either. verify_challenge
    # checks against the bundle alone, so anything allowed here and refused there
    # put a Fail badge beside a challenge that had already been shown.
    authoritative = {k: v for k, v in payload.items()
                     if k not in ("explanation", "verification")}
    numbers_map = extract_numbers_with_paths(authoritative)
    
    # Verify explicitly declared numbers
    for num in result["numbers_used"]:
        if not isinstance(num, (int, float)):
            raise ValueError(f"Invalid number type in numbers_used: {num}")
        val = float(num)
        is_allowed = any(
            math.isclose(val, a, rel_tol=1e-5, abs_tol=1e-5) or 
            math.isclose(val * 100, a, rel_tol=1e-5, abs_tol=1e-5) or 
            math.isclose(val / 100, a, rel_tol=1e-5, abs_tol=1e-5) 
            for a in numbers_map.keys()
        )
        if not is_allowed:
            raise ValueError(f"Unsupported numeric claim: {val} is not in the payload")
            
    # Verify prose strings
    validate_prose_numbers(result["challenge"], numbers_map)
    validate_prose_numbers(result["alternative_suggested"], numbers_map)
    for ev in result["evidence_cited"]:
        validate_prose_numbers(ev, numbers_map)
        
    return result


def fallback_challenge(bundle, chosen_plan_id):
    """A challenge built from templates when the model's own tries were refused.

    Mirrors fallback_explain: the same three checks apply to it, so it has to be
    made of bundle numbers only and do no arithmetic. Before this existed, one
    refused generation meant the challenge panel stayed empty and the customer
    saw no argument at all - which looks exactly like a broken button.

    Numbers are written as plain digits with no comma grouping. Indian grouping
    reads better, but "12,34,567" is not one number to the prose checker, and a
    fallback that fails the check it exists to satisfy is worse than a plain one.
    """
    plans = {p["plan_id"]: p for p in bundle.get("plans", [])}
    plan = plans.get(chosen_plan_id)
    if plan is None:
        raise ValueError(f"plan {chosen_plan_id} is not in the bundle")

    surplus = bundle["profile"]["monthly_surplus"]
    numbers = [plan["monthly_investment"], surplus]
    points = []

    # Each point is a field read straight out of the bundle. Nothing is compared,
    # added or converted - the engines already decided all of it.
    if not plan.get("feasible"):
        points.append(
            f"It asks for {plan['monthly_investment']} a month, and your monthly "
            f"surplus is {surplus}. On today's income you cannot fund it without "
            f"cutting something else.")
    else:
        points.append(
            f"It asks for {plan['monthly_investment']} a month out of a surplus "
            f"of {surplus}, so most of your spare money is committed for years.")

    if plan.get("survives_stress") is False and plan.get("shortfall_if_hit") is not None:
        points.append(
            f"It does not survive our stress test. If those shock events land "
            f"together you finish {plan['shortfall_if_hit']} short of the goal.")
        numbers.append(plan["shortfall_if_hit"])

    # Simulation counts rather than the probability: both are bundle numbers, but
    # "0 of 10000 simulations" needs no conversion, where the probability would
    # have to be read out as "0.0" or multiplied by 100 to become a percentage.
    if (plan.get("successful_simulations") is not None
            and bundle.get("n_simulations") is not None):
        points.append(
            f"Out of {bundle['n_simulations']} simulations on historical market "
            f"returns, {plan['successful_simulations']} reached your goal. That is "
            f"a simulation result, not a promise.")
        numbers.extend([bundle["n_simulations"], plan["successful_simulations"]])

    if plan.get("exceeds_risk_ceiling"):
        points.append(
            "It also sits above the risk level your own financial position "
            "supports, so a bad year would hurt more than you may expect.")

    # The alternative is read from the comparison the orchestrator precomputed,
    # never chosen by comparing numbers here.
    comparisons = bundle.get("comparisons", {})
    alternative = comparisons.get("cheapest_plan_id")
    if alternative == chosen_plan_id:
        alternative = comparisons.get("highest_success_plan_id")
    if alternative == chosen_plan_id or alternative not in plans:
        alternative = "none"

    return {
        "chosen_plan_id": chosen_plan_id,
        "challenge": " ".join(points),
        "evidence_cited": [
            f"plans[{chosen_plan_id}].monthly_investment",
            "profile.monthly_surplus",
            f"plans[{chosen_plan_id}].successful_simulations",
        ],
        "alternative_suggested": alternative,
        "numbers_used": numbers,
        "source": "fallback",
    }
