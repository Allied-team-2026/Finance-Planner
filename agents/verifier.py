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

def collect_whitelist(obj, out=None):
    if out is None:
        out = set()
    if isinstance(obj, bool):
        return out
    if isinstance(obj, (int, float)):
        out.add(round(float(obj), 6))
    elif isinstance(obj, str):
        for tok in re.findall(r"\d[\d,]*(?:\.\d+)?", obj):
            try:
                out.add(round(float(tok.replace(",", "")), 6))
            except ValueError:
                pass
    elif isinstance(obj, dict):
        for v in obj.values():
            collect_whitelist(v, out)
    elif isinstance(obj, list):
        for v in obj:
            collect_whitelist(v, out)
    return out

def sweep(text):
    found = []
    for m in re.finditer(r"(\d[\d,]*(?:\.\d+)?)(%?)", text):
        raw, pct = m.group(1), m.group(2)
        try:
            val = float(raw.replace(",", ""))
        except ValueError:
            continue
        found.append((m.group(0), {val, val / 100} if pct else {val}, m.start(), m.end()))
    return found

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
        
    text_numbers = [round(c, 6) for _, candidates, _, _ in sweep(text) for c in candidates]
    
    # Specific fields to check for cross-contamination
    fields_to_check = ["monthly_investment", "projected_corpus", "success_probability"]
    
    for p in other_plans:
        for field in fields_to_check:
            val = p.get(field)
            if val is None:
                continue
            
            # If the value is in the text, BUT it's not this plan's value, AND it's not a global value like goal_amount
            # It might be cross-contamination. 
            # Note: We must allow comparisons like "Costs 5000 less than Plan B (30000)"
            # So a strict cross-contamination check is risky if they explicitly name the other plan.
            # But the prompt requires wrong monthly investment to fail.
            # We will flag it if they use another plan's value AND they don't mention the other plan's ID.
            if round(float(val), 6) in text_numbers:
                if round(float(val), 6) != round(float(this_plan.get(field, -1)), 6):
                    # They used a number from another plan. Did they mention the other plan?
                    if f"plan {p['plan_id'].lower()}" not in text.lower():
                        flags.append(f"Cross-contamination: used {field} {val} from Plan {p['plan_id']} without referencing it")
                        
    # Check allocation percentages explicitly
    # If the text says 65% equity, but this plan is 40% equity, that's wrong.
    this_equity = round(this_plan.get("allocation", {}).get("equity", -1), 6)
    if this_equity >= 0:
        for p in other_plans:
            other_eq = round(p.get("allocation", {}).get("equity", -1), 6)
            if other_eq in text_numbers and other_eq != this_equity:
                if f"plan {p['plan_id'].lower()}" not in text.lower():
                    flags.append(f"Cross-contamination: used equity allocation {other_eq} from Plan {p['plan_id']}")
                    
    return flags

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
        val = round(float(n), 6)
        if val not in all_wl:
            if round(val / 100, 6) not in all_wl:
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
            
        for token, candidates, start, end in sweep(text):
            checked += 1
            # P10/P90 structural labels
            context = text[max(0, start - 10):min(len(text), end + 15)].lower()
            exempt = False
            for c in candidates:
                if c == 10.0 and any(label in context for label in ["10th", "p10", "10-90", "10‑90"]):
                    exempt = True
                if c == 90.0 and any(label in context for label in ["90th", "p90", "10-90", "10‑90"]):
                    exempt = True
            if exempt:
                continue
                
            if not any(round(c, 6) in allowed for c in candidates):
                if any(round(c, 6) in all_wl for c in candidates):
                    flags.append(f"Cross-plan contamination: {token} used in Plan {pid} without explicit reference")
                else:
                    unverified.append(f"Prose number {token} not found in bundle")
        
    for k in ["goal_priority_note", "mismatch_note", "peer_cohort_note"]:
        text = explanation.get(k, "")
        for token, candidates, _, _ in sweep(text):
            checked += 1
            if not any(round(c, 6) in all_wl for c in candidates):
                unverified.append(f"Prose number {token} in {k} not found in bundle")

    if unverified or flags:
        result["status"] = "fail"
        
    result["numbers_checked"] = checked
    result["unverified_numbers"] = list(set(unverified)) if unverified else []
    result["suitability_flags"] = flags
    
    return result
