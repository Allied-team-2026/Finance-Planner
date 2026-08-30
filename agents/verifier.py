import json
import re

BEHAVIOUR_VERBS = (r"abandon|quit|give up|stop investing|drop out|walk away|"
                   r"stick with|stay invested|follow through|panic|bail")

FORBIDDEN_CLAIMS = [
    (rf"\b(?:chance|probability|odds|likelihood)\s+(?:that\s+)?you\b",
     "probability attached to the customer's own future behaviour"),
    (rf"\byou\s+(?:will|are likely to|would probably)\s+(?:{BEHAVIOUR_VERBS})",
     "prediction about what the customer will do"),
    (rf"\d+(?:\.\d+)?\s*%[^.]{{0,80}}?\b(?:{BEHAVIOUR_VERBS})\b",
     "percentage in the same sentence as a behaviour verb"),
    (r"\bguarantee(?:d|s)?\b", "a guarantee about an uncertain outcome"),
    (r"\b(?:will definitely|is certain to|cannot fail)\b", "certainty we do not have"),
    (r"\b(?:recommend|you should)\s+(?:buying|selling)\b", "a specific product instruction"),
]

from agents.numeric import validate_prose_numbers, extract_decimals

def collect_whitelist(obj, out=None):
    if out is None:
        out = set()
    if isinstance(obj, bool):
        return out
    if isinstance(obj, (int, float)):
        out.add(float(obj))
    elif isinstance(obj, str):
        for match, val, _, _ in extract_decimals(obj):
            out.add(val)
    elif isinstance(obj, dict):
        for v in obj.values():
            collect_whitelist(v, out)
    elif isinstance(obj, list):
        for v in obj:
            collect_whitelist(v, out)
    return out


def build_whitelists(bundle):
    bundle_copy = dict(bundle)
    plans = bundle_copy.pop("plans", [])
    comparisons = bundle_copy.pop("comparisons", {})
    
    global_wl = set()
    collect_whitelist(bundle_copy, global_wl)
    
    comp_wl = set()
    collect_whitelist(comparisons, comp_wl)
    
    plan_wls = {}
    for p in plans:
        pid = p.get("plan_id")
        if not pid: continue
        wl = set()
        collect_whitelist(p, wl)
        plan_wls[pid] = wl
        
    return global_wl, comp_wl, plan_wls
        


def verify(explanation, bundle):
    checked = 0
    unverified = []
    flags = []
    
    result = {
        "status": "pass",
        "numbers_checked": 0,
        "unverified_numbers": [],
        "suitability_flags": []
    }
    
    if not isinstance(explanation, dict):
        result["status"] = "fail"
        result["suitability_flags"].append("Explanation is not a JSON object")
        return result
        
    for field in ["plans_text", "goal_priority_note", "mismatch_note", "peer_cohort_note", "numbers_used"]:
        if field not in explanation:
            flags.append(f"Missing required field: {field}")
            
    if flags:
        result["status"] = "fail"
        result["suitability_flags"] = flags
        return result
        
    plans_text = explanation["plans_text"]
    if not isinstance(plans_text, list):
        flags.append("plans_text must be a list")
    elif len(plans_text) != 3:
        flags.append(f"Expected exactly 3 plans, got {len(plans_text)}")
    else:
        plan_ids = [pt.get("plan_id") for pt in plans_text]
        if plan_ids != ["A", "B", "C"]:
            flags.append(f"Expected plan IDs ['A', 'B', 'C'] in order, got {plan_ids}")
            
    # Privacy checks
    expl_str = json.dumps(explanation, ensure_ascii=False)
    expl_lower = expl_str.lower()
    
    customer_id = bundle.get("customer_id", "").lower()
    name = bundle.get("customer_name", "").lower()
    if customer_id and customer_id in expl_lower:
        flags.append("Privacy violation: customer_id found")
    if name:
        for part in name.split():
            if part in expl_lower:
                flags.append("Privacy violation: customer name found")
                break
    if "ground_truth_risk" in expl_lower:
        flags.append("Privacy violation: ground_truth_risk found")
        
    # Check 5 (forbidden claims)
    for pattern, why in FORBIDDEN_CLAIMS:
        for m in re.finditer(pattern, expl_str, re.IGNORECASE):
            flags.append(f"Forbidden claim: {why} ({m.group(0)})")
            
    # Categorical risk check
    risk_stated = bundle.get("risk", {}).get("stated", "").lower()
    risk_revealed = bundle.get("risk", {}).get("revealed", "").lower()
    risk_capacity = bundle.get("profile", {}).get("risk_capacity", "").lower()
    
    valid_risks = {risk_stated, risk_revealed, risk_capacity}
    valid_risks.discard("")
    
    for risk_term in ["aggressive", "moderate", "conservative"]:
        if risk_term in expl_lower and risk_term not in valid_risks:
            flags.append(f"Categorical risk violation: used '{risk_term}' but it does not match stated/revealed/capacity")
            
    # Peer cohort categorical checks
    cohort = bundle.get("peer_cohort")
    if cohort:
        pass

    # Numeric whitelist mappings
    global_wl, comp_wl, plan_wls = build_whitelists(bundle)
    all_wl = set(global_wl) | set(comp_wl)
    for wl in plan_wls.values():
        all_wl.update(wl)

    for n in explanation.get("numbers_used", []):
        checked += 1
        # Use validate_prose_numbers so rounding rules apply consistently
        errors = validate_prose_numbers(str(n), all_wl, raise_on_fail=False)
        if errors:
            unverified.append(n)
            
    # Sweep prose
    for pt in explanation.get("plans_text", []):
        text = json.dumps(pt, ensure_ascii=False)
        text_lower = text.lower()
        pid = pt.get("plan_id")
        
        mentioned_pids = set([pid]) if pid else set()
        for other_pid in plan_wls:
            # Require explicit mentioning to allow cross-contamination values
            if f"plan {other_pid.lower()}" in text_lower:
                mentioned_pids.add(other_pid)
                
        allowed = set(global_wl)
        for m_pid in mentioned_pids:
            if m_pid in plan_wls:
                allowed.update(plan_wls[m_pid])
                
        # Comparison values only allowed if multiple plans explicitly named
        if len(mentioned_pids) > 1:
            allowed.update(comp_wl)
            
        errors_allowed = validate_prose_numbers(text, allowed, raise_on_fail=False)
        errors_all = validate_prose_numbers(text, all_wl, raise_on_fail=False)
        
        all_wl_failed_matches = {err[0] for err in errors_all}
        
        for match, val, err in errors_allowed:
            checked += 1
            if match not in all_wl_failed_matches:
                flags.append(f"Cross-plan contamination: {match} used in Plan {pid} without explicit reference")
            else:
                unverified.append(f"Prose number {match} not found in bundle")
        
        # We must increment checked for valid numbers too, to maintain consistency in check count.
        for match, val, start, end in extract_decimals(text):
            checked += 1
        
    for k in ["goal_priority_note", "mismatch_note", "peer_cohort_note"]:
        text = explanation.get(k, "")
        errors = validate_prose_numbers(text, all_wl, raise_on_fail=False)
        for match, val, err in errors:
            unverified.append(f"Prose number {match} in {k} not found in bundle")
        for match, val, start, end in extract_decimals(text):
            checked += 1

    if unverified or flags:
        result["status"] = "fail"
        
    result["numbers_checked"] = checked
    result["unverified_numbers"] = list(set(unverified)) if unverified else []
    result["suitability_flags"] = flags

    return result


def verify_challenge(challenge, bundle):
    """Section 10's numbers, held to the same rule as section 9's.

    Separate from verify() because the challenge does not exist yet when the
    explanation is checked - it is written only after the customer picks a plan.
    So the Auditor badge on screen was reporting on the explanation alone, and
    said "Pass" while the challenge panel showed another customer's money.

    Unlike the plans_text sweep this checks against every plan's numbers rather
    than only the chosen plan's. Arguing "the Steady plan asks for 35,000" is the
    challenger doing its job, not cross-plan contamination.
    """
    if not isinstance(challenge, dict):
        return {"status": "fail", "numbers_checked": 0, "unverified_numbers": [],
                "suitability_flags": ["Challenge is not a JSON object"]}

    checked = 0
    unverified = []
    flags = []

    global_wl, comp_wl, plan_wls = build_whitelists(bundle)
    all_wl = set(global_wl) | set(comp_wl)
    for wl in plan_wls.values():
        all_wl.update(wl)

    for n in challenge.get("numbers_used", []):
        checked += 1
        if validate_prose_numbers(str(n), all_wl, raise_on_fail=False):
            unverified.append(f"Declared number {n} not found in bundle")

    for text in [challenge.get("challenge", "")] + list(challenge.get("evidence_cited", [])):
        for match, val, err in validate_prose_numbers(text, all_wl, raise_on_fail=False):
            unverified.append(f"Prose number {match} not found in bundle")
        for _ in extract_decimals(text):
            checked += 1

    blob = json.dumps(challenge, ensure_ascii=False)
    for pattern, why in FORBIDDEN_CLAIMS:
        for m in re.finditer(pattern, blob, re.IGNORECASE):
            flags.append(f"Forbidden claim: {why} ({m.group(0)})")

    return {
        "status": "fail" if (unverified or flags) else "pass",
        "numbers_checked": checked,
        "unverified_numbers": sorted(set(unverified)),
        "suitability_flags": flags,
    }

