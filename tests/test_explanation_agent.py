"""
Tests for section 8, the Explanation Agent.

Two kinds of test live here.

The first kind is ordinary: right shape, right plan ids, no empty strings.

The second kind is the one that matters. Madhura's bar for section 8 is not "it
ran" - it is three consecutive runs in which the Verifier finds zero unverified
numbers. So this file carries the Verifier's own checks and runs the agent's real
output through them:

    check 1  every number declared in numbers_used exists in plan_bundle
    check 2  every number swept out of the prose exists in plan_bundle
    check 3  no claim that no engine can support (the 71%-chance-you-abandon trap)

Those three functions are a deliberate COPY of the ones in tools/verify_mocks.py,
not an import. That script is a flat top-level program - it loads /mocks at
import time and ends in sys.exit(0) - so importing it would run it and then kill
the test process. It also cannot be pointed at anything other than /mocks, and
/mocks is off limits. Section 9 remains Pushkar's; this is a local copy for
testing one module. If his checks get stricter, this copy has to be re-synced -
that is the cost of the copy and it is written down here so it is not a surprise.

Runs under pytest, or directly with `python3 tests/test_explanation_agent.py` on
a machine with no packages installed, same as tests/test_pipeline.py.
"""

import copy
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from agents.explanation import (DigitInTemplate, MissingField, explain,  # noqa: E402
                               render)

BUNDLE_PATH = os.path.join(ROOT, "mocks", "plan_bundle.json")


def load_bundle():
    """Read-only. Nothing in this file ever writes to /mocks."""
    with open(BUNDLE_PATH, encoding="utf-8") as fh:
        return json.load(fh)


# ------------------------------------------- the Verifier's checks, copied

def collect_whitelist(obj, out=None):
    """Every number the engines produced, including numbers inside engine strings.

    Shock labels and evidence sentences are engine output, so numbers quoted from
    them are already trustworthy. A whitelist of numeric fields alone would
    reject every correctly quoted piece of evidence.
    """
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
        for value in obj.values():
            collect_whitelist(value, out)
    elif isinstance(obj, list):
        for value in obj:
            collect_whitelist(value, out)
    return out


def sweep(text):
    """Pull every number out of prose.

    Indian grouping: '26,20,000' is 2620000. Percentages: '40%' may match a
    stored 0.4 or a stored 40, so both readings are offered.
    """
    found = []
    for match in re.finditer(r"(\d[\d,]*(?:\.\d+)?)(%?)", text):
        raw, pct = match.group(1), match.group(2)
        try:
            val = float(raw.replace(",", ""))
        except ValueError:
            continue
        found.append((match.group(0), {val, val / 100} if pct else {val}))
    return found


BEHAVIOUR_VERBS = (r"abandon|quit|give up|stop investing|drop out|walk away|"
                   r"stick with|stay invested|follow through|panic|bail")

FORBIDDEN_CLAIMS = [
    (r"\b(?:chance|probability|odds|likelihood)\s+(?:that\s+)?you\b",
     "probability attached to the customer's own future behaviour"),
    (rf"\byou\s+(?:will|are likely to|would probably)\s+(?:{BEHAVIOUR_VERBS})",
     "prediction about what the customer will do"),
    (rf"\d+(?:\.\d+)?\s*%[^.]{{0,80}}?\b(?:{BEHAVIOUR_VERBS})\b",
     "percentage in the same sentence as a behaviour verb"),
    (r"\bguarantee(?:d|s)?\b", "a guarantee about an uncertain outcome"),
    (r"\b(?:will definitely|is certain to|cannot fail)\b", "certainty we do not have"),
    (r"\b(?:recommend|you should)\s+(?:buying|selling)\b", "a specific product instruction"),
]


def check_claims(doc):
    hits = []
    text = " ".join(re.findall(r'"[^"]{40,}"', json.dumps(doc)))
    for pattern, why in FORBIDDEN_CLAIMS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            hits.append(f"{why}: {match.group(0)!r}")
    return hits


def prose_of(doc):
    texts = [doc["goal_priority_note"], doc["mismatch_note"]]
    for plan in doc["plans_text"]:
        texts.extend([plan["headline"], plan["body"]])
        texts.extend(plan["pros"])
        texts.extend(plan["cons"])
    return texts


def unverified(doc, bundle):
    """The Verifier's verdict on this output. Empty list means a clean run."""
    whitelist = collect_whitelist(bundle)
    bad = []
    for number in doc["numbers_used"]:
        if round(float(number), 6) not in whitelist:
            bad.append(f"declared {number} is not in plan_bundle")
    for text in prose_of(doc):
        for token, candidates in sweep(text):
            if not any(round(c, 6) in whitelist for c in candidates):
                bad.append(f"prose contains {token!r} which is in no engine output")
    return bad


# ----------------------------------------------------------------- shape

def test_output_has_the_contract_shape():
    bundle = load_bundle()
    doc = explain(bundle)

    assert set(doc) == {"plans_text", "goal_priority_note", "mismatch_note",
                        "numbers_used"}

    ids = [p["plan_id"] for p in doc["plans_text"]]
    assert ids == [p["plan_id"] for p in bundle["plans"]], (
        "one entry per plan, in payload order")

    for plan in doc["plans_text"]:
        assert set(plan) == {"plan_id", "headline", "body", "pros", "cons"}
        assert plan["headline"].strip() and plan["body"].strip()
        assert plan["pros"] and plan["cons"], "a plan with no trade-offs is a sales pitch"
        for item in plan["pros"] + plan["cons"]:
            assert isinstance(item, str) and item.strip()

    assert doc["goal_priority_note"].strip()
    assert doc["mismatch_note"].strip()
    assert doc["numbers_used"], "numbers_used is mandatory - it is what makes §9 reliable"
    assert doc["numbers_used"] == sorted(doc["numbers_used"])
    assert len(doc["numbers_used"]) == len(set(doc["numbers_used"]))


# ------------------------------------------------------------ the DONE bar

def test_three_consecutive_runs_find_zero_unverified_numbers():
    """Madhura's stated bar for §8, encoded as an assertion.

    The renderer is deterministic, so the three runs are also byte-identical -
    which is the stronger claim: not merely three clean runs, but no run that
    could differ from them.
    """
    bundle = load_bundle()
    runs = [explain(load_bundle()) for _ in range(3)]

    for index, doc in enumerate(runs, start=1):
        assert unverified(doc, bundle) == [], f"run {index} was not clean"

    assert runs[0] == runs[1] == runs[2], "output is not deterministic"


def test_declared_numbers_all_exist_in_the_payload():
    bundle = load_bundle()
    whitelist = collect_whitelist(bundle)
    for number in explain(bundle)["numbers_used"]:
        assert round(float(number), 6) in whitelist, (
            f"{number} was declared but no engine produced it")


def test_every_number_in_the_prose_is_declared_or_quoted_from_the_payload():
    """Stricter than §9, and the whole point of substituting rather than writing.

    §9 accepts any prose number that exists somewhere in the payload. This asserts
    the tighter property the design actually gives: a prose number is either
    declared in numbers_used, or it sits inside a string the engines wrote and we
    quoted verbatim - a shock label like "Appraisal comes in at 4% instead of 10%".
    There is no third source.
    """
    bundle = load_bundle()
    doc = explain(bundle)

    declared = {round(float(n), 6) for n in doc["numbers_used"]}
    quoted = collect_whitelist(
        [p.get("breaking_combo") for p in bundle["plans"]]
        + [bundle["risk"]["evidence"], bundle["profile"]["risk_capacity_reasons"]])
    allowed = declared | quoted

    for text in prose_of(doc):
        for token, candidates in sweep(text):
            assert any(round(c, 6) in allowed for c in candidates), (
                f"{token!r} appears in the prose but is neither declared nor "
                f"quoted from an engine-written string")


def test_no_claim_the_engines_cannot_support():
    bundle = load_bundle()
    assert check_claims(explain(bundle)) == []


# ------------------------------------------------- do the guards actually bite?
#
# A guard that never fires looks exactly like a guard that is not there.

def test_a_digit_typed_into_a_template_is_rejected():
    bundle = load_bundle()

    render("your surplus is {profile.monthly_surplus} a month", bundle)  # fine

    for smuggled in ("you have 45,000 spare",
                     "roughly 87% of runs succeeded",
                     "that is 2 occasions"):
        try:
            render(smuggled, bundle)
        except DigitInTemplate:
            continue
        raise AssertionError(f"a literal number got through: {smuggled!r}")


def test_a_number_no_engine_produced_is_fatal_not_invented():
    """The behaviour Madhura asked for: ask for the field, never work it out."""
    bundle = load_bundle()

    for absent in ("{profile.years_of_returns_data}",
                   "{plans.A.months_to_goal}",
                   "{plans.A.breaking_probability}"):  # null for a plan that survives
        try:
            render(f"a sentence needing {absent}", bundle)
        except MissingField:
            continue
        raise AssertionError(f"{absent} should have failed loudly")


def test_the_verifier_copy_catches_a_fabricated_number():
    """If this test's own checks are broken, every test above is meaningless."""
    bundle = load_bundle()
    doc = explain(bundle)

    doc["plans_text"][0]["body"] += " That works out to 41,667 a year."
    assert unverified(doc, bundle), "the number sweep is not biting"

    clean = explain(load_bundle())
    clean["numbers_used"] = clean["numbers_used"] + [999999]
    assert unverified(clean, bundle), "the declaration check is not biting"

    trap = explain(load_bundle())
    trap["mismatch_note"] += (
        " Given that history, there is a 71% chance you abandon this plan "
        "before the goal is reached.")
    assert unverified(trap, bundle) == [], (
        "0.71 is a real success_probability, so a numeric check cannot see this")
    assert check_claims(trap), "the claim check must catch what the sweep cannot"


# --------------------------------------------------- other payloads, same rules
#
# Plan C's figures are under review and the plan count is not fixed at three, so
# nothing may be keyed to a plan id or to there being exactly three plans.

def test_it_survives_a_payload_with_different_plans():
    bundle = load_bundle()
    variant = copy.deepcopy(bundle)

    variant["plans"] = [p for p in variant["plans"] if p["plan_id"] != "C"]
    variant["comparisons"]["plan_count"] = len(variant["plans"])
    variant["comparisons"]["monthly_investment_delta_vs_cheapest"].pop("C", None)
    variant["plans"][0]["projected_corpus"] = 2711000
    variant["plans"][0]["p90_corpus"] = 3401000

    doc = explain(variant)
    assert [p["plan_id"] for p in doc["plans_text"]] == ["A", "B"]
    assert unverified(doc, variant) == []
    assert "2,711,000" not in json.dumps(doc), "Indian grouping regressed"
    assert "27,11,000" in json.dumps(doc), "the changed figure was not picked up"


def test_a_customer_whose_stated_risk_matches_is_not_told_it_mismatches():
    """Demo persona C002 exists to prove the model is not always crying mismatch."""
    bundle = load_bundle()
    variant = copy.deepcopy(bundle)
    variant["risk"].update({"stated": "moderate", "revealed": "moderate",
                            "mismatch": False})

    doc = explain(variant)
    assert unverified(doc, variant) == []
    assert check_claims(doc) == []
    note = doc["mismatch_note"].lower()
    assert "but your" not in note and "occasions you sold" not in note


def test_a_single_goal_payload_does_not_reference_a_second_goal():
    bundle = load_bundle()
    variant = copy.deepcopy(bundle)
    variant["goals"] = variant["goals"][:1]

    doc = explain(variant)
    assert unverified(doc, variant) == []
    assert "child education" not in doc["goal_priority_note"]
    assert "twelve" not in doc["goal_priority_note"]


def test_the_payload_is_never_modified():
    """The agent is a reader. Eight people share this fixture."""
    bundle = load_bundle()
    before = json.dumps(bundle, sort_keys=True)
    explain(bundle)
    assert json.dumps(bundle, sort_keys=True) == before


# --------------------------------------------------------------------- runner

if __name__ == "__main__":
    tests = [(name, obj) for name, obj in sorted(globals().items())
             if name.startswith("test_") and callable(obj)]
    failed = []

    for name, fn in tests:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 - a test runner wants everything
            failed.append((name, f"{type(exc).__name__}: {exc}"))
            print(f"FAIL  {name}")
        else:
            print(f"ok    {name}")

    print()
    if failed:
        for name, why in failed:
            print(f"{name}\n    {why}")
        print(f"\n{len(failed)} of {len(tests)} failed")
        sys.exit(1)

    doc = explain(load_bundle())
    print(f"{len(tests)} passed - "
          f"{len(doc['numbers_used'])} numbers declared, all traced to plan_bundle")
    sys.exit(0)
