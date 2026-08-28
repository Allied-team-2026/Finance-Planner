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
    }
    
    if "cohort" in bundle:
        payload["peer_cohort"] = bundle["cohort"]
    elif "peer_cohort" in bundle:
        payload["peer_cohort"] = bundle["peer_cohort"]
        
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

def explain(bundle):
    """Section 8. Turn plan_bundle into readable plan text.

    Called by the orchestrator as `agents.explanation:explain`.
    """
    if not bundle.get("plans"):
        raise MissingField("payload has no plans to explain")

    prose = Prose(bundle)
    plans_text = []

    for plan in bundle["plans"]:
        pid = plan["plan_id"]
        plans_text.append({
            "plan_id": pid,
            "headline": _headline(prose, pid, plan),
            "body": _body(prose, pid, plan, bundle),
            "pros": _pros(prose, pid, plan, bundle),
            "cons": _cons(prose, pid, plan, bundle),
        })

    return {
        "plans_text": plans_text,
        "goal_priority_note": _goal_priority_note(prose, bundle),
        "mismatch_note": _mismatch_note(prose, bundle),
        "numbers_used": _declare(prose.numbers),
    }
