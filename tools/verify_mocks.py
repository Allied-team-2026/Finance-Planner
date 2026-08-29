#!/usr/bin/env python3
"""
verify_mocks.py — consistency check for the /mocks folder.

Two jobs:

1. Cross-file consistency. Every mock describes the same customer (C001), so the
   numbers have to agree across files. A mock whose numbers do not add up teaches
   everyone the wrong shape and produces a demo a judge can break with mental
   arithmetic.

2. A working reference implementation of the section 9 Verifier. It checks the
   Explanation and Challenger output against plan_bundle.json exactly the way the
   real Verifier must: build a whitelist of every number the engines produced, then
   confirm that nothing in the agent's prose came from anywhere else.

Run from the repo root:  python3 tools/verify_mocks.py
Exit code 0 = all checks pass.
"""

import json
import os
import re
import sys

MOCKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mocks")

failures = []
notes = []


def strip_notes(obj):
    """Remove every _mock_note field.

    Keys starting with an underscore are documentation for whoever opens the file,
    not part of the data contract. They have to come out before any comparison,
    otherwise a note explaining that plan_bundle must not contain a customer_id
    reads as a plan_bundle that contains a customer_id.
    """
    if isinstance(obj, dict):
        return {k: strip_notes(v) for k, v in obj.items() if not k.startswith("_")}
    if isinstance(obj, list):
        return [strip_notes(v) for v in obj]
    return obj


def load(name):
    with open(os.path.join(MOCKS, name)) as f:
        return strip_notes(json.load(f))


def all_keys(obj, out=None):
    if out is None:
        out = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.add(k)
            all_keys(v, out)
    elif isinstance(obj, list):
        for v in obj:
            all_keys(v, out)
    return out


def check(label, got, want):
    if got != want:
        failures.append(f"{label}: got {got!r}, expected {want!r}")


# ---------------------------------------------------------------- load everything

files = [
    "customer_C001.json", "profile_out.json", "features_out.json", "risk_out.json",
    "plans_out.json", "montecarlo_out.json", "stress_out.json", "plan_bundle.json",
    "explanation_out.json", "peer_cohort_out.json", "challenge_out.json",
    "api_response.json",
]
data = {}
for name in files:
    try:
        data[name] = load(name)
    except FileNotFoundError:
        failures.append(f"MISSING FILE: {name}")
    except json.JSONDecodeError as e:
        failures.append(f"INVALID JSON in {name}: {e}")

if failures:
    print("\n".join(failures))
    sys.exit(1)

cust = data["customer_C001.json"]
prof = data["profile_out.json"]
feat = data["features_out.json"]
risk = data["risk_out.json"]
plans = data["plans_out.json"]
mc = data["montecarlo_out.json"]
stress = data["stress_out.json"]
bundle = data["plan_bundle.json"]
expl = data["explanation_out.json"]
cohort = data["peer_cohort_out.json"]
chal = data["challenge_out.json"]
api = data["api_response.json"]

# ------------------------------------------------- 1. customer record -> profile

assets = sum(cust["assets"].values())
liab = sum(l["outstanding"] for l in cust["liabilities"])
transactions = cust["transactions"]
if transactions:
    all_months = sorted(list(set(t["date"][:7] for t in transactions)))
    last_12_months = set(all_months[-12:])
    filtered_transactions = [t for t in transactions if t["date"][:7] in last_12_months]
    num_months = len(last_12_months)
else:
    filtered_transactions = []
    num_months = 1

txn_total = sum(t["amount"] for t in filtered_transactions)
avg_monthly_txn = int(round(txn_total / num_months))

check("profile.total_assets == sum of assets", prof["total_assets"], assets)
check("profile.total_liabilities == sum of outstanding", prof["total_liabilities"], liab)
check("profile.net_worth == assets - liabilities", prof["net_worth"], assets - liab)
check("profile.monthly_income == customer income", prof["monthly_income"], cust["monthly_income"])
check("profile.monthly_expense == transaction month total", prof["monthly_expense"], avg_monthly_txn)
check("profile.monthly_surplus == income - expense",
      prof["monthly_surplus"], prof["monthly_income"] - prof["monthly_expense"])
check("profile.existing_emi_total == sum of emis",
      prof["existing_emi_total"], sum(l["emi"] for l in cust["liabilities"]))
check("profile.emergency_fund_months == savings / expense",
      prof["emergency_fund_months"],
      round(cust["assets"]["savings_account"] / prof["monthly_expense"], 2))
check("expense_breakdown sums to monthly_expense",
      sum(prof["expense_breakdown"].values()), prof["monthly_expense"])

# breakdown must match the transactions category by category
by_cat = {}
for t in filtered_transactions:
    by_cat[t["category"]] = by_cat.get(t["category"], 0) + t["amount"]

for cat in by_cat:
    by_cat[cat] = int(round(by_cat[cat] / num_months))

diff = avg_monthly_txn - sum(by_cat.values())
if diff != 0 and by_cat:
    largest_cat = max(by_cat, key=by_cat.get)
    by_cat[largest_cat] += diff

check("expense_breakdown matches transactions by category",
      dict(sorted(prof["expense_breakdown"].items())), dict(sorted(by_cat.items())))

# risk_capacity, recomputed from the section 2 rule
sr = prof["monthly_surplus"] / prof["monthly_income"]
score = (2 if sr >= 0.30 else 1 if sr >= 0.15 else 0)
ef = prof["emergency_fund_months"]
score += (2 if ef >= 6 else 1 if ef >= 3 else 0)
dep = cust["dependents"]
score += (2 if dep == 0 else 1 if dep <= 2 else 0)
horizon = min(g["years"] for g in cust["goals"])
score += (2 if horizon >= 10 else 1 if horizon >= 5 else 0)
score += 1 if cust["employment_type"] == "salaried" else 0
band = "aggressive" if score >= 7 else "moderate" if score >= 4 else "conservative"
check(f"risk_capacity recomputed (score {score}/9)", prof["risk_capacity"], band)

# ------------------------------------------------- 2. features and risk

# A panic sell is a sell that followed a market drop, which the record marks by
# setting days_after_drop. A sell in a calm market leaves it null and is not a panic.
# This used to count every sell. Both of C001's sells follow drops, so both versions
# give 2 and both pass today - but the loose one stops meaning what its name says the
# moment §1 generates a customer who sells in a calm market.
panic = [e["days_after_drop"] for e in cust["investment_events"]
         if e["action"] == "sell" and e["days_after_drop"] is not None]
check("features.panic_sell_count == sells that followed a drop",
      feat["panic_sell_count"], len(panic))
check("features.avg_days_to_exit_after_drop == mean over those same sells",
      feat["avg_days_to_exit_after_drop"],
      round(sum(panic) / len(panic), 1) if panic else None)
check("features.equity_allocation_pct == equity_mf / total assets",
      feat["equity_allocation_pct"], round(cust["assets"]["equity_mf"] / assets, 4))
check("features.emergency_fund_months matches profile",
      feat["emergency_fund_months"], prof["emergency_fund_months"])
check("risk.features_used == features_out", risk["features_used"], feat)
check("risk.stated_risk == customer stated_risk", risk["stated_risk"], cust["stated_risk"])
check("risk.mismatch == (stated != revealed)",
      risk["mismatch"], risk["stated_risk"] != risk["revealed_risk"])
check("revealed_risk == ground_truth_risk for this persona",
      risk["revealed_risk"], cust["ground_truth_risk"])

# ------------------------------------------------- 3. plans, simulation, stress

for p in plans["plans"]:
    pid = p["plan_id"]
    check(f"plan {pid} allocation sums to 1.0", round(sum(p["allocation"].values()), 10), 1.0)
    check(f"plan {pid} surplus_after_investment",
          p["surplus_after_investment"], prof["monthly_surplus"] - p["monthly_investment"])
    check(f"plan {pid} feasible", p["feasible"], p["monthly_investment"] <= prof["monthly_surplus"])
    check(f"plan {pid} shortfall",
          p["shortfall"], max(0, p["monthly_investment"] - prof["monthly_surplus"]))
    check(f"plan {pid} goal_amount == priority 1 goal",
          p["goal_amount"], cust["goals"][0]["target_amount"])
    check(f"plan {pid} years == priority 1 goal years", p["years"], cust["goals"][0]["years"])
    # ceiling is the more conservative of risk_capacity and revealed risk
    order = {"conservative": 0, "moderate": 1, "aggressive": 2}
    ceiling = min(prof["risk_capacity"], risk["revealed_risk"], key=lambda x: order[x])
    cap = {"conservative": 0.35, "moderate": 0.65, "aggressive": 1.0}[ceiling]
    check(f"plan {pid} exceeds_risk_ceiling (ceiling {ceiling}, cap {cap})",
          p["exceeds_risk_ceiling"], p["allocation"]["equity"] > cap)

mc_by = {r["plan_id"]: r for r in mc["results"]}
for pid, r in mc_by.items():
    goal = next(p["goal_amount"] for p in plans["plans"] if p["plan_id"] == pid)
    check(f"mc {pid} successful_simulations",
          r["successful_simulations"], round(r["success_probability"] * mc["n_simulations"]))
    check(f"mc {pid} p10_gap_to_goal", r["p10_gap_to_goal"], max(0, goal - r["p10_corpus"]))
    if not (r["p10_corpus"] <= r["median_corpus"] <= r["p90_corpus"]):
        failures.append(f"mc {pid}: percentiles out of order")

st_by = {r["plan_id"]: r for r in stress["results"]}
for pid, r in st_by.items():
    if r["survives"]:
        for k in ("breaking_combo", "breaking_probability", "shortfall_if_hit"):
            check(f"stress {pid} {k} must be null when it survives", r[k], None)
    else:
        prod = 1.0
        for e in r["breaking_combo"]:
            prod *= e["annual_probability"]
        check(f"stress {pid} breaking_probability == product of event probabilities",
              r["breaking_probability"], round(prod, 6))

check("same plan ids across plans / mc / stress",
      sorted(mc_by) == sorted(st_by) == sorted(p["plan_id"] for p in plans["plans"]), True)

# ------------------------------------------------- 4. the orchestrator merge

# The privacy line: identifiers must not reach the agent, attributes may.
# Checked two ways, because either one alone gives a false result. A key search
# alone misses a name pasted into a sentence; a substring search alone trips over
# the legitimate goal field called "name".
bundle_keys = all_keys(bundle)
for forbidden_key in ("customer_id", "ground_truth_risk", "customer_name",
                      "account_number", "pan"):
    if forbidden_key in bundle_keys:
        failures.append(f"PRIVACY: plan_bundle has a {forbidden_key} field")
if "name" in all_keys({k: v for k, v in bundle.items() if k != "goals"}):
    failures.append("PRIVACY: plan_bundle has a name field outside goals")

bundle_text = json.dumps(bundle)
for forbidden_value in cust["name"].split() + [cust["customer_id"]]:
    if forbidden_value in bundle_text:
        failures.append(f"PRIVACY: plan_bundle contains the literal {forbidden_value!r}")
if cust["ground_truth_risk"] != bundle["risk"]["revealed"]:
    notes.append("ground_truth_risk and revealed risk differ - fine, but worth knowing")
check("bundle risk.stated == risk_out.stated_risk", bundle["risk"]["stated"], risk["stated_risk"])
check("bundle risk.revealed == risk_out.revealed_risk",
      bundle["risk"]["revealed"], risk["revealed_risk"])
check("bundle risk.panic_sell_count == features", bundle["risk"]["panic_sell_count"],
      feat["panic_sell_count"])

b_by = {p["plan_id"]: p for p in bundle["plans"]}
for pid, bp in b_by.items():
    src = next(p for p in plans["plans"] if p["plan_id"] == pid)
    for k in ("monthly_investment", "surplus_after_investment", "allocation",
              "projected_corpus", "goal_amount", "years", "feasible", "shortfall",
              "exceeds_risk_ceiling"):
        check(f"bundle {pid}.{k} came from plans_out", bp[k], src[k])
    for k in ("success_probability", "successful_simulations", "median_corpus",
              "p10_corpus", "p90_corpus", "p10_gap_to_goal"):
        check(f"bundle {pid}.{k} came from montecarlo_out", bp[k], mc_by[pid][k])
    check(f"bundle {pid}.survives_stress renamed from stress.survives",
          bp["survives_stress"], st_by[pid]["survives"])
    for k in ("breaking_combo", "breaking_probability", "shortfall_if_hit"):
        check(f"bundle {pid}.{k} came from stress_out", bp[k], st_by[pid][k])
    if "expected_annual_return" in bp:
        failures.append(f"bundle {pid}: expected_annual_return should be trimmed out")

cheapest = min(bundle["plans"], key=lambda p: p["monthly_investment"])
check("comparisons.cheapest_plan_id", bundle["comparisons"]["cheapest_plan_id"], cheapest["plan_id"])
check("comparisons.highest_success_plan_id", bundle["comparisons"]["highest_success_plan_id"],
      max(bundle["plans"], key=lambda p: p["success_probability"])["plan_id"])
check("comparisons.plan_count", bundle["comparisons"]["plan_count"], len(bundle["plans"]))
for pid, delta in bundle["comparisons"]["monthly_investment_delta_vs_cheapest"].items():
    check(f"comparisons delta for {pid}",
          delta, b_by[pid]["monthly_investment"] - cheapest["monthly_investment"])

# ------------------------------------------------- 5. peer cohort

check("cohort savings rate == surplus / income",
      cohort["customer_savings_rate"],
      round(prof["monthly_surplus"] / prof["monthly_income"], 4))
if cohort["cohort_size"] < 20:
    failures.append("cohort_size below the minimum of 20 - must return null instead")
check("cohort goal_type == priority 1 goal", cohort["goal_type"], cust["goals"][0]["name"])
if not (0 <= cohort["savings_rate_percentile"] <= 100):
    failures.append("savings_rate_percentile out of range")
cohort_text = json.dumps(cohort)
for leak in cust["name"].split() + [cust["customer_id"], "customer_id"]:
    if leak in cohort_text:
        failures.append(f"PRIVACY: peer cohort contains {leak!r}")
if cohort["cohort_size"] < len(cohort["matched_on"]) * 5:
    notes.append("cohort is small relative to how many things it matched on")

# ------------------------------------------------- 6. the Verifier (section 9)

def collect_whitelist(obj, out=None):
    """Every number the engines produced.

    Includes numbers found inside engine-written STRINGS (evidence sentences,
    risk_capacity_reasons, shock labels). Those strings are engine output, so the
    numbers in them are already trustworthy - and the Challenger quotes them
    verbatim. A whitelist built only from numeric fields would reject every
    correctly quoted piece of evidence.
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
        for v in obj.values():
            collect_whitelist(v, out)
    elif isinstance(obj, list):
        for v in obj:
            collect_whitelist(v, out)
    return out


def sweep(text):
    """Pull every number out of prose.

    Two things a naive regex gets wrong:
      - Indian grouping. '26,20,000' is 2620000, not 26.20 or 2620.
      - Percentages. '40%' may legitimately match a stored 0.4 or a stored 40,
        so both readings are offered and either one passing is enough.
    """
    found = []
    for m in re.finditer(r"(\d[\d,]*(?:\.\d+)?)(%?)", text):
        raw, pct = m.group(1), m.group(2)
        try:
            val = float(raw.replace(",", ""))
        except ValueError:
            continue
        found.append((m.group(0), {val, val / 100} if pct else {val}))
    return found


whitelist = collect_whitelist(bundle)


def verify(name, doc, prose_fields):
    checked = 0
    unverified = []

    for n in doc.get("numbers_used", []):
        checked += 1
        if round(float(n), 6) not in whitelist:
            unverified.append(f"declared {n} is not in plan_bundle")

    texts = []
    for f in prose_fields:
        v = doc.get(f)
        if isinstance(v, str):
            texts.append(v)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, str):
                    texts.append(item)
                elif isinstance(item, dict):
                    for k in ("headline", "body"):
                        if k in item:
                            texts.append(item[k])
                    for k in ("pros", "cons"):
                        texts.extend(item.get(k, []))

    for text in texts:
        for token, candidates in sweep(text):
            checked += 1
            if not any(round(c, 6) in whitelist for c in candidates):
                unverified.append(f"prose contains {token!r} which is in no engine output")

    return checked, unverified


expl_checked, expl_bad = verify(
    "explanation", expl, ["plans_text", "goal_priority_note", "mismatch_note"])
chal_checked, chal_bad = verify("challenge", chal, ["challenge", "evidence_cited"])

failures.extend(f"VERIFIER (explanation): {m}" for m in expl_bad)
failures.extend(f"VERIFIER (challenge): {m}" for m in chal_bad)

# the Challenger must not invent a probability
for m in re.finditer(r"(\d+(?:\.\d+)?)\s*%", chal["challenge"]):
    v = float(m.group(1))
    if round(v / 100, 6) not in whitelist and round(v, 6) not in whitelist:
        failures.append(f"CHALLENGER invented a percentage: {m.group(0)}")

# --- check 5: claims no engine can support ------------------------------------
#
# The whitelist has a hole that cannot be closed by making the whitelist stricter.
# It confirms a number EXISTS in engine output. It cannot confirm the number means
# what the sentence says it means. "There is a 71% chance you abandon this plan"
# passes every numeric check, because 0.71 is real - it is plan B's success
# probability - but it has been attached to a quantity nothing measures.
#
# Our engines measure money and market outcomes. Nothing in the pipeline predicts
# what a person will do next; the adherence model was cut. So any probability
# attached to a future human action is invented by construction, and the way to
# catch it is to look at the words, not the digits.

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


def check_claims(doc):
    hits = []
    text = " ".join(re.findall(r'"[^"]{40,}"', json.dumps(doc)))
    for pattern, why in FORBIDDEN_CLAIMS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            hits.append(f"{why}: {m.group(0)!r}")
    return hits


for label, doc in (("explanation", expl), ("challenge", chal)):
    for hit in check_claims(doc):
        failures.append(f"CLAIM CHECK ({label}): {hit}")

# ------------------------------------------------- 6b. does the Verifier bite?
#
# A verifier that passes everything looks exactly like a verifier that does
# nothing. So before trusting it, feed it prose we know is wrong and confirm it
# objects. Each case below is a mistake an LLM actually makes.

NEGATIVE_CASES = [
    ("invented count",
     "7,376 reached your goal", "7,900 reached your goal"),
    ("agent did subtraction",
     "leaves you 10,000 of breathing room", "leaves you 11,000 of breathing room"),
    ("lakh figure slightly off",
     "projected 2,660,000", "projected 2,670,000"),
    ("percent converted by the agent",
     "Only 56.91% of simulations", "Only 57.91% of simulations"),
    ("plausible but absent number",
     "40% of your monthly investment", "45% of your monthly investment"),
]

missed = []
for label, original, corrupted in NEGATIVE_CASES:
    text = json.dumps(expl)
    if original not in text:
        missed.append(f"{label}: test string {original!r} is not in the mock any more")
        continue
    broken = json.loads(text.replace(original, corrupted))
    _, caught = verify("negative", broken, ["plans_text", "goal_priority_note", "mismatch_note"])
    if not caught:
        missed.append(f"{label}: verifier did NOT catch {corrupted!r}")

# and the one that matters most for the Challenger. The numeric check cannot catch
# this - 0.71 is a real engine number - so it has to be the claim check that fires.
chal_text = json.dumps(chal).replace(
    "A plan is only as good as your willingness",
    "There is a 56.91% chance you abandon this within seven weeks. A plan is only as good "
    "as your willingness")
broken_chal = json.loads(chal_text)
_, numeric_caught = verify("negative", broken_chal, ["challenge", "evidence_cited"])
claim_caught = check_claims(broken_chal)
if not claim_caught:
    missed.append("invented adherence probability: neither check caught it")
elif numeric_caught:
    missed.append("unexpected: the numeric check fired, so this is no longer the "
                  "test case it was written to be")
else:
    notes.append("invented adherence probability was caught by the claim check only - "
                 "the numeric check passed it, which is exactly why check 5 exists")

if missed:
    failures.extend(f"SELF TEST: {m}" for m in missed)
else:
    notes.append(f"verifier self test: caught all {len(NEGATIVE_CASES) + 1} planted errors")

# ------------------------------------------------- 7. api_response agreement

check("api customer_id", api["customer_id"], cust["customer_id"])
check("api customer_name", api["customer_name"], cust["name"])
check("api context == bundle context", api["context"], bundle["context"])
check("api risk.stated", api["risk"]["stated"], risk["stated_risk"])
check("api risk.revealed", api["risk"]["revealed"], risk["revealed_risk"])
check("api goals == customer goals", api["goals"], cust["goals"])
check("api peer_cohort agrees with cohort mock",
      {k: v for k, v in api["peer_cohort"].items() if k in cohort},
      {k: v for k, v in cohort.items() if k in api["peer_cohort"]})
check("api challenge is null before the customer picks", api["challenge"], None)

api_by = {p["plan_id"]: p for p in api["plans"]}
expl_by = {p["plan_id"]: p for p in expl["plans_text"]}
for pid, ap in api_by.items():
    for k in ("monthly_investment", "surplus_after_investment", "success_probability",
              "successful_simulations", "p10_gap_to_goal", "survives_stress",
              "breaking_probability", "shortfall_if_hit", "exceeds_risk_ceiling"):
        check(f"api {pid}.{k} == bundle", ap[k], b_by[pid][k])
    for k in ("headline", "body", "pros", "cons"):
        check(f"api {pid}.{k} == explanation output", ap[k], expl_by[pid][k])
    if "expected_annual_return" not in ap:
        failures.append(f"api {pid}: expected_annual_return must be present for the UI")

check("api goal_priority_note == explanation", api["goal_priority_note"], expl["goal_priority_note"])
check("api mismatch_note == explanation", api["mismatch_note"], expl["mismatch_note"])
check("api meta.returns_data_source == montecarlo",
      api["meta"]["returns_data_source"], mc["returns_data_source"])
check("api meta.n_simulations == montecarlo", api["meta"]["n_simulations"], mc["n_simulations"])
check("api meta.model_version == risk model", api["meta"]["model_version"], risk["model_version"])
check("api meta.assumptions_version == plans",
      api["meta"]["assumptions_version"], plans["assumptions_version"])
check("api verifier.unverified_numbers is empty", api["verifier"]["unverified_numbers"], [])

# ground_truth_risk is a hidden answer key for training and scoring the model.
# It must exist in the customer record and nowhere else in the pipeline.
for name in files:
    if name == "customer_C001.json":
        continue
    if "ground_truth_risk" in all_keys(data[name]):
        failures.append(f"LEAK: ground_truth_risk appears in {name}")

# Word numbers escape a digit-only regex. They pass check 2 without being checked,
# so they are only covered by check 1 - the agent declaring them in numbers_used.
# This is a real hole, not a theoretical one: it is what let 'twenty years' sit in
# a committed file unnoticed. Report them so a human can eyeball them.
WORD_NUMBERS = ("one", "two", "three", "four", "five", "six", "seven", "eight",
                "nine", "ten", "eleven", "twelve", "twenty", "thirty", "forty",
                "fifty", "hundred", "thousand", "lakh", "crore", "half", "double")
for label, doc in (("explanation", expl), ("challenge", chal)):
    text = json.dumps(doc).lower()
    hits = sorted({w for w in WORD_NUMBERS if re.search(rf"\b{w}\b", text)})
    if hits:
        notes.append(f"{label} prose contains word numbers the regex cannot check: "
                     + ", ".join(hits))

# ------------------------------------------------- report

print(f"files checked            : {len(files)}")
print(f"verifier numbers checked : {expl_checked} explanation, {chal_checked} challenge")
print(f"whitelist size           : {len(whitelist)} distinct engine numbers")
print()
if notes:
    print("NOTES (not failures, but read them):")
    for n in notes:
        print("  -", n)
    print()
if failures:
    print(f"FAILURES ({len(failures)}):")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print("all checks pass")
sys.exit(0)
