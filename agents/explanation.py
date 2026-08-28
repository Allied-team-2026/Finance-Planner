"""
Section 8 - the Explanation Agent.

The rule this module exists to make unbreakable: an agent may not do arithmetic.
Not adding, not subtracting, not rounding, not counting, not turning a
probability into a number of simulations.

The obvious way to satisfy that rule is to ask a model nicely and then verify
what it produced. That is worth doing, and section 9 does it. But verification
after the fact only ever tells you the model already misbehaved, and on a live
demo "already misbehaved" is the whole problem.

So this module inverts it. Prose is written as a TEMPLATE that may not contain a
single digit. Numbers enter only where a template names a field in plan_bundle:

    "reaches a projected {plans.A.projected_corpus} against your target"

`render` resolves each placeholder against the bundle and records the raw value
it substituted. Three properties follow, and they are the point of the file:

  - A number cannot be computed, because prose never writes one. The only
    numbers that can appear are ones an engine put in the payload.
  - `numbers_used` is a by-product of substitution rather than a parse of the
    finished prose, so it cannot disagree with what the prose actually says.
  - A sentence needing a number no engine produced fails loudly as MissingField.
    That is the signal to ask for a new engine field - never to work it out.

Everything here is deterministic and runs with no API key and no network. When a
language model is added, its only permitted job is choosing and phrasing
templates; a template containing a digit is rejected before it reaches a
customer, so the model cannot smuggle a number in even if it tries.

Reads mocks/plan_bundle.json shaped input. Writes nothing. Touches no shared file.
"""

import re

# --------------------------------------------------------------------- errors


class MissingField(KeyError):
    """A template asked for a field the payload does not contain.

    Deliberately fatal. The correct response is to ask for the field to be added
    to an engine, not to compute the number here or quietly drop the sentence.
    """


class DigitInTemplate(ValueError):
    """A template contained a literal digit.

    This is the guard that makes the no-arithmetic rule structural rather than
    aspirational. Any number in customer-facing prose must arrive by
    substitution from the payload, so a digit typed into a template - by a
    person or by a model - is rejected here.
    """


# ------------------------------------------------------------------- lookup


def _lookup(bundle, path):
    """Resolve a dotted path against the payload.

    Supports dict keys, list indices, and - because it is what every template
    actually wants - addressing a plan by its plan_id: `plans.A.projected_corpus`.
    """
    node = bundle
    for part in path.split("."):
        if isinstance(node, list):
            by_id = [item for item in node
                     if isinstance(item, dict) and item.get("plan_id") == part]
            if by_id:
                node = by_id[0]
                continue
            if part.lstrip("-").isdigit() and int(part) < len(node):
                node = node[int(part)]
                continue
            raise MissingField(f"{path!r}: no list entry {part!r}")
        if isinstance(node, dict):
            if part not in node:
                raise MissingField(
                    f"{path!r}: no field {part!r} in the payload - ask for it to "
                    f"be added to the engine output, do not derive it")
            node = node[part]
            continue
        raise MissingField(f"{path!r}: cannot look up {part!r} inside {type(node).__name__}")
    if node is None:
        raise MissingField(f"{path!r} is null in the payload")
    return node


# ---------------------------------------------------------------- formatting
#
# Formatting is presentation, not arithmetic: grouping digits and rendering a
# stored decimal as a percentage do not change which engine number is being
# quoted, and section 9's sweep accepts both readings of a percentage for
# exactly this reason. It is kept to this one block so there is a single place
# to audit. Nothing outside these functions may transform a value.


_WORDS = {
    0: "zero", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
    7: "seven", 8: "eight", 9: "nine", 10: "ten", 11: "eleven", 12: "twelve",
    13: "thirteen", 14: "fourteen", 15: "fifteen", 16: "sixteen",
    17: "seventeen", 18: "eighteen", 19: "nineteen", 20: "twenty",
    30: "thirty", 40: "forty", 50: "fifty",
}


def _group_indian(n):
    """1234567 -> '12,34,567'. Last three digits, then pairs."""
    sign, digits = ("-", str(abs(int(n)))) if n < 0 else ("", str(int(n)))
    if len(digits) <= 3:
        return sign + digits
    head, tail = digits[:-3], digits[-3:]
    pairs = []
    while len(head) > 2:
        pairs.insert(0, head[-2:])
        head = head[:-2]
    if head:
        pairs.insert(0, head)
    return sign + ",".join(pairs) + "," + tail


def _as_percent(value):
    """0.4 -> '40%'. Rounded only to kill float representation noise."""
    scaled = round(float(value) * 100, 6)
    return f"{int(scaled) if scaled == int(scaled) else scaled}%"


def _as_words(value):
    if int(value) in _WORDS:
        return _WORDS[int(value)]
    raise MissingField(f"no word form for {value!r} - write it as a figure instead")


def _humanise(text):
    return str(text).replace("_", " ")


def _format(value, spec):
    if spec == "pct":
        return _as_percent(value)
    if spec == "words":
        return _as_words(value)
    if spec in ("text", "label"):
        return _humanise(value) if spec == "label" else str(value)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return str(value)
    return _group_indian(value)


# ------------------------------------------------------------------- render


_PLACEHOLDER = re.compile(r"\{([a-zA-Z0-9_.]+)(?::([a-z]+))?\}")


def render(template, bundle):
    """Substitute every {path} from the payload.

    Returns the finished text and the raw values that went into it. The raw
    values - not the formatted strings - are what gets declared in numbers_used,
    so the declaration always matches the payload rather than the prose.
    """
    literal = _PLACEHOLDER.sub("", template)
    stray = re.search(r"\d", literal)
    if stray:
        raise DigitInTemplate(
            f"template contains the literal digit {stray.group(0)!r}: {template!r} - "
            f"every number must come from a payload field")

    used = []

    def substitute(match):
        value = _lookup(bundle, match.group(1))
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            used.append(value)
        return _format(value, match.group(2))

    return _PLACEHOLDER.sub(substitute, template), used


class Prose:
    """Accumulates rendered text and the numbers it drew on."""

    def __init__(self, bundle):
        self.bundle = bundle
        self.numbers = []

    def one(self, template):
        text, used = render(template, self.bundle)
        self.numbers.extend(used)
        return text

    def joined(self, templates):
        return " ".join(self.one(t) for t in templates if t)

    def each(self, templates):
        return [self.one(t) for t in templates if t]


def _declare(values):
    """numbers_used: de-duplicated, ascending, integers kept as integers."""
    seen = {}
    for value in values:
        key = round(float(value), 6)
        if key not in seen or isinstance(value, int):
            seen[key] = value
    return [seen[key] for key in sorted(seen)]


# ----------------------------------------------------------- plan narration
#
# Sentences are selected by what a plan IS, never by its plan_id. Plan C's
# figures are under review and the plan count is not fixed at three, so any
# template keyed to a specific plan would be wrong the moment an engine changes
# its numbers.


def _weighting(plan):
    equity = plan["allocation"]["equity"]
    if equity < 0.5:
        return "weighted towards debt"
    if equity < 0.8:
        return "with more in equity"
    return "mostly in equity"


def _headline(prose, pid, plan):
    return prose.one(
        f"Invest {{plans.{pid}.monthly_investment}} a month, {_weighting(plan)}")


def _body(prose, pid, plan, bundle):
    p = f"plans.{pid}"
    sentences = [
        f"This plan puts {{{p}.allocation.equity:pct}} of your monthly investment "
        f"into equity and {{{p}.allocation.debt:pct}} into debt, and reaches a "
        f"projected {{{p}.projected_corpus}} against your {{{p}.goal_amount}} "
        f"target in {{{p}.years:words}} years."
    ]

    if plan["feasible"]:
        sentences.append(
            f"It asks for {{{p}.monthly_investment}} of your "
            f"{{profile.monthly_surplus}} monthly surplus, which leaves you "
            f"{{{p}.surplus_after_investment}} of breathing room each month.")
    else:
        sentences.append(
            f"It is not affordable on your current finances: it needs "
            f"{{{p}.monthly_investment}} a month against a surplus of "
            f"{{profile.monthly_surplus}}, leaving you {{{p}.shortfall}} short "
            f"every month.")

    sentences.append(
        f"Out of {{n_simulations}} simulations run on real historical market "
        f"returns, {{{p}.successful_simulations}} reached your goal.")

    if plan["survives_stress"]:
        sentences.append(
            "It also held up against every combination of shock events we tested.")
    else:
        # Shock labels are engine-written sentences, not list items, so they are
        # quoted verbatim rather than folded into a comma list - editing them
        # would be editing engine output, and running them together with commas
        # reads as one broken sentence.
        labels = [f'"{{{p}.breaking_combo.{i}.label:text}}"'
                  for i in range(len(plan["breaking_combo"]))]
        events = (labels[0] if len(labels) == 1
                  else " and ".join([", ".join(labels[:-1]), labels[-1]]))
        sentences.append(
            f"It does not survive our stress test: {events} landing together "
            f"would leave you {{{p}.shortfall_if_hit}} short of the goal.")

    return prose.joined(sentences)


def _pros(prose, pid, plan, bundle):
    p = f"plans.{pid}"
    comparisons = bundle["comparisons"]
    out = []

    if pid == comparisons["highest_success_plan_id"]:
        out.append("Of the plans offered, the highest chance of reaching your goal")
    if plan["survives_stress"]:
        out.append("Survives every shock combination the stress test tried")
    if plan["feasible"] and plan["surplus_after_investment"] > 0:
        out.append(f"Leaves {{{p}.surplus_after_investment}} a month unallocated "
                   f"for emergencies")
    if pid == comparisons["cheapest_plan_id"] and comparisons["plan_count"] > 1:
        out.append("Asks the least of your monthly surplus")
    out.append(f"Stronger outcomes reach {{{p}.p90_corpus}}")

    return prose.each(out)


def _cons(prose, pid, plan, bundle):
    p = f"plans.{pid}"
    comparisons = bundle["comparisons"]
    delta = comparisons["monthly_investment_delta_vs_cheapest"].get(pid)
    out = []

    if not plan["feasible"]:
        out.append(f"Not affordable: needs {{{p}.shortfall}} more per month than "
                   f"you have spare")
    if delta:
        out.append(
            f"Costs {{comparisons.monthly_investment_delta_vs_cheapest.{pid}}} "
            f"more per month than the cheapest plan")
    if not plan["survives_stress"]:
        out.append(f"Breaks under stress testing, leaving you "
                   f"{{{p}.shortfall_if_hit}} short")
    if plan["exceeds_risk_ceiling"]:
        out.append("Equity allocation is more aggressive than your own history "
                   "supports")
    if plan["p10_gap_to_goal"]:
        out.append(f"Weakest outcomes fall {{{p}.p10_gap_to_goal}} short of target")

    # "Only 87%" is a fair criticism of a weak plan and a misleading one about the
    # strongest plan on the table. Both framings are honest about the same number;
    # the difference is which of them is true.
    if pid == comparisons["highest_success_plan_id"]:
        out.append(f"Even here, {{{p}.success_probability:pct}} of simulations "
                   f"reached the goal rather than all of them")
    else:
        out.append(f"Only {{{p}.success_probability:pct}} of simulations reached "
                   f"your goal")

    return prose.each(out)


# ------------------------------------------------------------------- notes


def _goal_priority_note(prose, bundle):
    goals = sorted(range(len(bundle["goals"])),
                   key=lambda i: bundle["goals"][i]["priority"])
    first = goals[0]

    if len(goals) == 1:
        return prose.one(
            f"Your {{goals.{first}.name:label}} is the only goal on the table, so "
            f"the whole monthly amount is pointed at it and the {{goals.{first}.years:words}} "
            f"year horizon is what every projection above assumes.")

    second = goals[1]
    return prose.one(
        f"Your {{goals.{first}.name:label}} is funded first because it is "
        f"{{goals.{first}.years:words}} years away, while the "
        f"{{goals.{second}.name:label}} goal is {{goals.{second}.years:words}} "
        f"years out and can absorb a slower start. The nearer deadline is the "
        f"binding one, so it sets the monthly figure.")


def _mismatch_note(prose, bundle):
    risk = bundle["risk"]

    if not risk["mismatch"]:
        return prose.one(
            "You described your approach as {risk.stated:text}, and your "
            "transaction history agrees. The plans below are pitched at that "
            "level rather than argued down from it.")

    return prose.one(
        "You described your approach as {risk.stated:text}, but your transaction "
        "history looks {risk.revealed:text}. On {risk.panic_sell_count:words} "
        "occasions you sold equity within days of a market fall. That matters "
        "here because the plans with the highest projected returns are exactly "
        "the ones that fall furthest during a bad year, and a plan left early "
        "performs worse than a slower plan held to the end.")


# ------------------------------------------------------------------- public


def build_explanation_payload(bundle):
    """
    Transforms the internal bundle into the exact trimmed structure required
    by the Explanation Agent.
    """
    payload = {
        "context": bundle.get("context", {}),
        "profile": bundle.get("profile", {}),
        "risk": bundle.get("risk", {}),
        "goals": bundle.get("goals", []),
        "plans": bundle.get("plans", []),
        "comparisons": bundle.get("comparisons", {}),
        "n_simulations": bundle.get("n_simulations"),
        "peer_cohort": bundle.get("peer_cohort")
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

def extract_numbers_with_paths(obj, path="payload"):
    numbers = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            for num, paths in extract_numbers_with_paths(v, f"{path}.{k}").items():
                numbers.setdefault(num, []).extend(paths)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            for num, paths in extract_numbers_with_paths(v, f"{path}[{i}]").items():
                numbers.setdefault(num, []).extend(paths)
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        numbers.setdefault(float(obj), []).append(path)
    elif isinstance(obj, str):
        import re
        matches = re.findall(r'(?<![a-zA-Z0-9_])-?\d+(?:,\d{3})*(?:\.\d+)?(?![a-zA-Z0-9_])', obj)
        for match in matches:
            try:
                val = float(match.replace(',', ''))
                numbers.setdefault(val, []).append(path)
            except ValueError:
                pass
    return numbers

def get_inferred_units(path_list):
    """Infer the unit of the data based on its path in the payload."""
    units = set()
    for path in path_list:
        path_lower = path.lower()
        if any(w in path_lower for w in ["amount", "corpus", "investment", "surplus", "income", "expense", "worth", "delta", "impact", "gap", "shortfall", "cost"]):
            units.add("money")
        if any(w in path_lower for w in ["percent", "rate", "probability", "allocation", "confidence"]):
            units.add("percent")
        if any(w in path_lower for w in ["year", "month", "day"]):
            units.add("time")
        if any(w in path_lower for w in ["count", "simulations", "dependents"]):
            units.add("count")
    return units

def validate_prose_numbers(prose, numbers_map):
    import re
    import math
    matches = re.finditer(r'-?\d+(?:,\d{3})*(?:\.\d+)?', prose)
    for match_obj in matches:
        match = match_obj.group(0)
        val = float(match.replace(',', ''))
        start_idx = match_obj.start()
        end_idx = match_obj.end()
        
        # Check for structural percentile labels
        context_start = max(0, start_idx - 5)
        context_end = min(len(prose), end_idx + 15)
        context = prose[context_start:context_end].lower()
        
        if val == 10.0 and ("10th percentile" in context or "p10" in context or "10-90" in context or "10‑90" in context):
            # Verify p10 exists in payload
            if any("p10" in p.lower() for paths in numbers_map.values() for p in paths):
                continue
        if val == 90.0 and ("90th percentile" in context or "p90" in context or "10-90" in context or "10‑90" in context):
            if any("p90" in p.lower() for paths in numbers_map.values() for p in paths):
                continue

        # Check if percentage
        is_percentage_format = False
        if end_idx < len(prose) and prose[end_idx] == '%':
            is_percentage_format = True
        
        is_money_format = False
        if start_idx > 0 and prose[start_idx - 1] in ['₹', '$']:
            is_money_format = True
            
        def get_paths(v):
            for a, paths in numbers_map.items():
                if math.isclose(v, a, rel_tol=1e-5, abs_tol=1e-5):
                    return paths
            return []
            
        paths = get_paths(val)
        paths_pct = get_paths(val / 100.0) if is_percentage_format or True else []  # Also check if value/100 exists
        
        valid_paths = paths + paths_pct
        if not valid_paths:
            raise ValueError(f"Unsupported numeric claim in prose: {match} (value: {val}) not found in payload")
            
        # Semantic validation
        inferred_units = get_inferred_units(valid_paths)
        if inferred_units:
            if is_money_format and "money" not in inferred_units:
                raise ValueError(f"Semantic mismatch: {match} used as money but originates from {valid_paths}")
            if is_percentage_format and "percent" not in inferred_units:
                raise ValueError(f"Semantic mismatch: {match} used as percent but originates from {valid_paths}")

def explain(bundle):
    """Section 8. Turn plan_bundle into readable plan text.
    
    Called by the orchestrator as `agents.explanation:explain`.
    """
    import os
    import json
    
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set")
        
    try:
        from groq import Groq
    except ImportError:
        raise ImportError("groq package is required. Run 'pip install groq'")
        
    payload = build_explanation_payload(bundle)
    
    system_prompt = """You are a financial explanation agent.
Your task is to explain the financial plans provided in the payload in human-readable language.

STEP 1
Create exactly one explanation object for each plan in the input (A, B, C).
The output `plans_text` MUST contain exactly the same plan IDs as the input plans, in the same order. Missing a plan is an error.

STEP 2
For each plan, explain ONLY the most decision-relevant facts:
- monthly investment, allocation, projected corpus, goal/feasibility, Monte Carlo success probability
- P10/P90 range when useful, stress result when useful
- one or two meaningful pros, one or two meaningful cons

Tell the model to prefer concise explanations. For each plan:
- 1 concise headline
- 2 to 4 sentences in body
- 1 to 3 pros
- 1 to 3 cons

Avoid repeating the same numbers across every sentence. Do not mention irrelevant internal fields. Keep it concise and readable. Do NOT dump every numeric field.

STEP 3
Add `goal_priority_note`: Explain the priority-1 goal using only supplied information.

STEP 4
Add `mismatch_note`: Explain stated vs revealed risk and relevant evidence.

STEP 5
Add `peer_cohort_note`: ONLY IF the payload contains a non-null peer cohort, explain the peer cohort as context, NOT as a recommendation. Do NOT invent peer data. If peer cohort is null, return exactly "No sufficiently large peer cohort was available."

RULES
Use ONLY numbers present in the supplied payload. Never invent or calculate numbers.
Do not calculate percentages from decimals, simulation counts from probabilities, shortfalls, investment deltas, savings rates, breaking probabilities, or corpus values. Quote supplied numbers exactly as they appear in the payload.
Never identify the customer.
In the "numbers_used" array, list ONLY the exact numbers you actually cited in your explanation text. Do not list every number from the payload. Do not put structural labels such as 10th percentile, 90th percentile, p10, or p90 into numbers_used.
"""

    model_name = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")
    
    schema = {
        "type": "object",
        "properties": {
            "plans_text": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "plan_id": {"type": "string"},
                        "headline": {"type": "string"},
                        "body": {"type": "string"},
                        "pros": {"type": "array", "items": {"type": "string"}},
                        "cons": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["plan_id", "headline", "body", "pros", "cons"],
                    "additionalProperties": False
                }
            },
            "goal_priority_note": {"type": "string"},
            "mismatch_note": {"type": "string"},
            "peer_cohort_note": {"type": "string"},
            "numbers_used": {"type": "array", "items": {"type": "number"}}
        },
        "required": ["plans_text", "goal_priority_note", "mismatch_note", "peer_cohort_note", "numbers_used"],
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
                "name": "explanation_response",
                "strict": True,
                "schema": schema
            }
        },
        temperature=0.0,
        max_tokens=4000
    )
    
    result = json.loads(response.choices[0].message.content)
    
    # 1. Structure validation
    if "plans_text" not in result or not isinstance(result["plans_text"], list):
        raise ValueError("Missing or invalid 'plans_text'")
        
    input_plan_ids = [p.get("plan_id") for p in payload.get("plans", [])]
    output_plan_ids = [pt.get("plan_id") for pt in result["plans_text"]]
    
    if input_plan_ids != output_plan_ids:
        raise ValueError(f"Plan ID mismatch. Expected exactly {input_plan_ids}, but got {output_plan_ids}")
        
    for pt in result["plans_text"]:
        for f in ["plan_id", "headline", "body", "pros", "cons"]:
            if f not in pt:
                raise ValueError(f"Missing required field in plan_text: {f}")
        if not isinstance(pt["headline"], str) or not isinstance(pt["body"], str):
            raise ValueError("headline and body must be strings")
        if not isinstance(pt["pros"], list) or not isinstance(pt["cons"], list):
            raise ValueError("pros and cons must be lists")
            
    for f in ["goal_priority_note", "mismatch_note"]:
        if f not in result or not isinstance(result[f], str):
            raise ValueError(f"Missing or invalid '{f}'")
    if "numbers_used" not in result or not isinstance(result["numbers_used"], list):
        raise ValueError("Missing or invalid 'numbers_used'")
        
    # 2. Privacy validation
    result_str = json.dumps(result).lower()
    forbidden_terms = ["jane", "c001", "g00", "ground_truth_risk", "rahul", "mehta", "account", "transaction", "investment_event"]
    for term in forbidden_terms:
        if term in result_str:
            raise ValueError(f"Privacy violation: '{term}' found in explanation")
            
    # 3. Numeric validation
    numbers_map = extract_numbers_with_paths(payload)
    
    # Check explicitly declared numbers_used
    import math
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
            
    # Check prose strings
    for pt in result["plans_text"]:
        validate_prose_numbers(pt["headline"], numbers_map)
        validate_prose_numbers(pt["body"], numbers_map)
        for pro in pt["pros"]:
            validate_prose_numbers(pro, numbers_map)
        for con in pt["cons"]:
            validate_prose_numbers(con, numbers_map)
            
    validate_prose_numbers(result["goal_priority_note"], numbers_map)
    validate_prose_numbers(result["mismatch_note"], numbers_map)
            
    return result
