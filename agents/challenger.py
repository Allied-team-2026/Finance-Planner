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

def challenge(bundle, explanation, verification, chosen_plan_id):
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
6. Use ONLY numbers present in the payload. Do not invent arbitrary numbers.
7. "alternative_suggested" must be exactly one plan id from {plan_ids}, or "none" if no other plan is better. No sentence, no explanation, no "Plan A" - just the letter.

FORMAT:
Output valid JSON matching the exact schema provided.
"""

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
    numbers_map = extract_numbers_with_paths(payload)
    
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
