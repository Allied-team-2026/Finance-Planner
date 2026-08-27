# JSON Data Contract — Finance Planning (Cognizant Hackathon)

**Version 1.2 · Amended 26 Aug 2026 · Owner: Shlok**
*(v1.1 amended 26 Aug 2026 · v1.0 frozen 24 Aug 2026)*

This document defines exactly what every module takes in and gives out. Once frozen, **nobody waits for anybody** — build against the mock data and it will fit on integration day.

> **Rule:** If you need to change a field, message the group first. Do not change it silently. A renamed field on Day 4 costs the whole team hours.

---

## What changed in v1.2 — all of it found by building, not by reading

**No section numbers moved, and nothing was renamed or removed.** v1.2 only fills gaps that only appeared once the mocks and the orchestrator existed. If you already built against v1.1, nothing you wrote is wrong — but three of these are fields your module has to produce.

**Fields the examples were missing**

1. **§1 was missing `name` and `goals`.** Both are required. `name` is what §11 returns as `customer_name`, and `goals` is the input to §4, §5 and §7 — without it there is nothing to plan for. The mock `mocks/customer_C001.json` has always had both; the contract example did not.
2. **§6's `breaking_combo` shocks carry `annual_probability`,** copied straight from `shocks.json`. Without it the UI can show *what* breaks a plan but not *how likely* each shock is, and §11's `breaking_probability` becomes a number nobody can check.
3. **§6 returns `combos_tested`.** "165 combinations tested" is worth a line on screen for one integer.
4. **§7's risk block carries `panic_sell_count`,** taken from §3a's features. The Challenger needs to say "you sold during a drop on two occasions" and it is not allowed to count.
5. **§7's `comparisons` carries `plan_count`.**
6. **§16 echoes `goal_type`** alongside `age_band` and `income_band`, so the screen can name the goal the cohort was matched on.

**Corrections**

7. **§6's example `breaking_probability` was `0.11` for a two-event combination,** which contradicts the rule stated ten lines below it — the product of `0.23` and `0.10` is `0.023`. Now consistent, and the shock probabilities are visible in the example so the arithmetic can be checked.
8. **§13 still named the returns file `nifty_yearly_returns.csv`** while §5 named it `nifty_yearly_2005_2025.csv`. The pinned name is **`nifty_yearly_2005_2025.csv`**. Everyone must use the identical file, or the same plan produces different success probabilities on different laptops and the demo contradicts itself.
9. **`generated_at` in §11 is a date (`"2026-08-26"`), not a timestamp.** The committed mock has always been a date; the sketch was ambiguous.

**§9 got materially stricter — read this if you own the Verifier**

10. **Two normalisation rules were missing and both cause failures rather than false passes.** Indian digit grouping: `"26,20,000"` is `2620000`, and a regex written for western commas reads it as `2620` and then flags every money figure in the prose as invented. Percentages: `"40%"` may legitimately match a stored `0.4` *or* a stored `40`, so offer both readings and pass if either is in the whitelist.
11. **The whitelist must include numbers found inside engine-written strings,** not just numeric fields. The Challenger quotes `evidence` verbatim, and those sentences contain digits — "within 3 days of a 9% market drop (Mar 2024)". Build the whitelist from strings too or the agent gets failed for quoting us correctly.
12. **New check 5: a forbidden-phrase check on words, not digits.** This closes the one hole the other four cannot. See §9.

**New in §12**

13. **`GET /api/status`** reports which stages are real engines and which are still mocks.
14. **How `/api/whatif` is implemented is now stated:** the orchestrator adds `extra_monthly_savings` to `profile.monthly_surplus` and re-runs the same pipeline. §4's signature does not change and does not need to know what-ifs exist.

---

## What changed in v1.1 — read this if you already read v1.0

**No section numbers moved.** Every `§n` reference in your prompts, commits and messages still points at the same thing. v1.1 only adds fields, corrects three mistakes, and adds one new section at the end.

**Additions**

1. **§2 now has `risk_capacity` and `risk_capacity_reasons`.** The brief says "risk taking **ability**", which means financial capacity to absorb a loss — surplus, emergency fund, dependents, time horizon. That is arithmetic, not a questionnaire. We had been treating it as risk *appetite* (willingness), which is a different question. Both now exist and both are shown.
2. **§1 and §12 now carry three context fields** — `dependents`, `employment_type`, `city_tier`. These feed `risk_capacity` and satisfy the "contextuality" requirement.
3. **§16 is new: the Peer Cohort Engine** — "look for customers with the same profile". Placed at the end so nothing renumbers; it runs after §6 and before §7. See the pipeline map below.
4. **§11 is fully specified** instead of being a sketch. This is the biggest change — see the correction note in §11.

**Corrections**

5. **§11's plan object was under-specified and would have broken the UI.** v1.0 said the plan object was "§7 merged with §8". But §7 is the deliberately trimmed, de-identified payload for the agents — it has no `feasible`, no `shortfall`, no `goal_amount`, no corpus range, no `breaking_probability`. A frontend built on that could not show whether a plan is affordable, what the range of outcomes is, or how likely the breaking combination is. **§11's plan object is now the full merge of §4 + §5 + §6 + §8.** §7 keeps its trimmed version, because agents genuinely should not see more than they need.
6. **§11 had no `customer_id`,** but `/api/challenge` and `/api/whatif` both require one in the request body. The frontend had no way to make either call. `customer_id` is now returned.
7. **The C001 example numbers did not add up.** §1 showed `savings_account: 300000` with a monthly expense of 75000, which by §2's own formula gives `emergency_fund_months = 4.0` — but §2's example showed `0.0` and §3's evidence said "no emergency fund". Three sections disagreed about the same customer. Fixed by setting savings to `30000`, which makes every dependent number consistent: emergency fund 0.4 months, equity allocation 0.5, total assets 800000, net worth 600000. Check your own examples against this — a judge doing mental arithmetic on screen is a real risk.

**Naming note.** §3's standalone output uses `stated_risk` / `revealed_risk`. §7 and §11 use `risk.stated` / `risk.revealed`. This is deliberate and stays as it is, because §7 is already frozen and being built against. The orchestrator does the rename once when it assembles the payload. Do not "fix" it in your module.

**The committed mock `mocks/api_response.json` on `main` is the authority for §11.** If this document and that file ever disagree, the file wins and this document gets corrected.

---

## Pipeline map — the order things actually run

```
§1  Synthetic Data ──> customer record
                          │
        ┌─────────────────┼──────────────────┐
        v                 v                  v
   §2 Profile        §3a Features       (goals from form)
        │                 │
        │                 v
        │            §3b Risk model ──> stated / revealed / capacity
        │                 │
        └────────┬────────┘
                 v
          §4 Plan Generator ──> 2-3 plans
                 │
        ┌────────┼────────┐
        v        v        v
   §5 Monte   §6 Stress  §16 Peer Cohort
    Carlo       Test      (needs the full dataset)
        │        │        │
        └────────┼────────┘
                 v
        §7 Orchestrator ──> plan_bundle (de-identified)
                 │
                 v
        §8 Explanation Agent ──> prose + numbers_used
                 │
                 v
        §9 Verifier ──> pass / fail (max 2 retries)
                 │
                 v
        §11 API response ──> Frontend
                 │
                 v
        §10 Challenger (only after the customer picks a plan)
```

Read it top to bottom: everything above a module must exist before that module can run for real. **Everything can be built at the same time anyway**, because §13 gives every module a mock of its input.

---

## 0. Conventions (read this first — most bugs come from here)

| Thing | Rule | Example |
|---|---|---|
| Money | Plain integer **rupees**. Never lakhs or crores. | `2500000` not `25` |
| Returns / rates | Decimal, not percent | `0.11` not `11` |
| Probability | `0.0` to `1.0` | `0.87` not `87` |
| Percentages in allocation | Decimal fractions summing to 1.0 | `{"equity": 0.4, "debt": 0.6}` |
| Field names | `snake_case`, lowercase | `monthly_surplus` |
| Dates | ISO string | `"2026-08-24"` |
| Risk level enum | Only these three strings | `"conservative"` \| `"moderate"` \| `"aggressive"` |
| Employment enum | Only these three strings | `"salaried"` \| `"self_employed"` \| `"business_owner"` |
| City tier enum | Only these three strings | `"metro"` \| `"tier_2"` \| `"tier_3"` |
| Plan IDs | Single uppercase letter | `"A"`, `"B"`, `"C"` |
| Missing value | `null`, never `0` or `""` | `"breaking_combo": null` |
| Errors | Raise a Python exception; the API layer converts it. Engines never return error strings. | — |

**Privacy rule (non-negotiable):** No PII ever goes to the LLM. No name, no `customer_id`, no account number. Agents receive only numbers and categories. The name is added back by the backend *after* the agents run. See §7.

---

## 1. Synthetic Data Generator → customer record

**Owner: Saurabh** (reassigned 26 Aug)

Produces **~1000+ customer records** for model training, plus **3 fixed demo personas** (`C001`, `C002`, `C003`).

Transactions must span **at least 24 months** so there is real "past trend data".

```json
{
  "customer_id": "C001",
  "name": "Rahul Mehta",
  "age": 28,
  "dependents": 1,
  "employment_type": "salaried",
  "city_tier": "metro",
  "stated_risk": "aggressive",
  "monthly_income": 120000,
  "assets": {
    "savings_account": 30000,
    "equity_mf": 400000,
    "fixed_deposit": 370000
  },
  "liabilities": [
    { "type": "car_loan", "outstanding": 200000, "emi": 8000 }
  ],
  "goals": [
    { "name": "house_downpayment", "target_amount": 2500000, "years": 5, "priority": 1 }
  ],
  "transactions": [
    { "date": "2026-07-05", "category": "rent",      "amount": 25000 },
    { "date": "2026-07-06", "category": "groceries", "amount": 4200  }
  ],
  "investment_events": [
    {
      "date": "2024-03-12",
      "action": "sell",
      "instrument": "equity_mf",
      "amount": 150000,
      "market_drawdown_pct": 9.0,
      "days_after_drop": 3
    }
  ],
  "ground_truth_risk": "moderate"
}
```

### New in v1.1 — context fields

| Field | Type | Allowed values | Why it exists |
|---|---|---|---|
| `dependents` | integer | `0` and up | More dependents means less room to absorb a loss. Feeds `risk_capacity`. |
| `employment_type` | string | `"salaried"` \| `"self_employed"` \| `"business_owner"` | Income stability. A self-employed customer needs a larger emergency fund before taking equity risk. |
| `city_tier` | string | `"metro"` \| `"tier_2"` \| `"tier_3"` | Cost of living context. A 75,000 expense in a metro means something different from 75,000 in a tier-3 city. |

These are the "contextuality" requirement. They are cheap to generate and they are what makes the plan visibly *for this person* rather than for a number.

### Critical notes

- `ground_truth_risk` is **for ML training and evaluation only**. It must **never** enter the planning pipeline or reach the frontend. Treat it as a hidden answer key.
- `name` and `goals` are required (**stated explicitly in v1.2** — the v1.1 example omitted both). `name` never reaches an agent: §7 strips it and §11 puts it back. `goals` is the input every later section plans against.
- Generate behaviour with **noise and confounders** — do not derive `ground_truth_risk` from a single clean rule, or the ML model just relearns your rule and the whole differentiator collapses under questioning.
- `category` values (fixed list): `rent`, `groceries`, `utilities`, `transport`, `dining`, `shopping`, `health`, `education`, `entertainment`, `emi`, `insurance`, `misc`.
- **The C001 numbers above must stay internally consistent** (corrected in v1.1): savings 30000 with a 75000 monthly expense gives `emergency_fund_months = 0.4`; equity 400000 of 800000 total assets gives `equity_allocation_pct = 0.5`; assets 800000 minus liabilities 200000 gives `net_worth = 600000`. §2, §3 and §11 all quote these. If you change one, change all of them.

### The 3 demo personas must be

| ID | Purpose |
|---|---|
| `C001` | Stated `aggressive`, revealed `moderate` → **mismatch** (shows differentiator 1) |
| `C002` | Stated `moderate`, revealed `moderate` → **match** (proves the model isn't always crying mismatch) |
| `C003` | Plan breaks dramatically under stress test (shows differentiator 2) |

---

## 2. Profile Engine

**Owner: Saurabh** · **In:** customer record (§1) or frontend form (§12) · **Out:**

```json
{
  "net_worth": 600000,
  "total_assets": 800000,
  "total_liabilities": 200000,
  "monthly_income": 120000,
  "monthly_expense": 75000,
  "monthly_surplus": 45000,
  "existing_emi_total": 8000,
  "emergency_fund_months": 0.4,
  "risk_capacity": "moderate",
  "risk_capacity_reasons": [
    "Monthly surplus of 37% of income is healthy",
    "Emergency fund covers less than half a month of expenses",
    "One dependent and an active car loan reduce room for loss",
    "Five year horizon is long enough to recover from a single bad year"
  ],
  "expense_breakdown": {
    "rent": 25000, "groceries": 12000, "emi": 8000,
    "transport": 6000, "dining": 5000, "misc": 19000
  }
}
```

- `net_worth = total_assets - total_liabilities`
- `monthly_surplus = monthly_income - monthly_expense` (this is the single most important number in the project — every plan depends on it)
- `monthly_expense` is the **mean of the last 12 months** of transactions, not one month
- `emergency_fund_months = savings_account / monthly_expense`
- `expense_breakdown` must sum exactly to `monthly_expense`. Round the largest category to absorb the rounding error, do not let it drift.

---

### `risk_capacity` — new in v1.1, and the most important addition ⭐

The brief asks for "risk taking **ability**". Ability is not the same thing as willingness. Willingness is what the customer says and what their behaviour reveals (§3). **Ability is whether their finances can survive a loss**, and it is pure arithmetic from data we already have.

Two customers can both say "aggressive". One has eight months of expenses saved, no dependents and a fifteen-year horizon. The other has two weeks of savings, two dependents and needs the money in three years. They have the same appetite and completely different ability. A plan that ignores this is answering only half the question the brief asked.

**Deterministic scoring — no ML, no LLM.** Five components, 0 to 2 points each except the last:

| Component | Test | Points |
|---|---|---|
| Surplus ratio (`monthly_surplus / monthly_income`) | `>= 0.30` / `0.15`–`0.30` / `< 0.15` | 2 / 1 / 0 |
| Emergency fund months | `>= 6` / `3`–`6` / `< 3` | 2 / 1 / 0 |
| Dependents | `0` / `1`–`2` / `3+` | 2 / 1 / 0 |
| Shortest goal horizon in years | `>= 10` / `5`–`10` / `< 5` | 2 / 1 / 0 |
| Employment type | `salaried` / `self_employed` or `business_owner` | 1 / 0 |

**Total out of 9 → `7-9` = `"aggressive"`, `4-6` = `"moderate"`, `0-3` = `"conservative"`.**

Worked example, C001: surplus ratio 0.375 → 2. Emergency fund 0.4 months → 0. One dependent → 1. Shortest goal 5 years → 1. Salaried → 1. **Total 5 → `"moderate"`.**

### Rules for `risk_capacity_reasons`

- **The engine writes these, not the LLM.** They are fixed sentence templates filled with real numbers. If an agent wrote them, the Verifier could not check them and we would be putting unverified claims on the screen — which is exactly the failure mode this whole architecture exists to prevent.
- One sentence per component that materially affected the score. Minimum 3.
- Write them as **plain readable sentences**, because the frontend shows them directly and the Explanation Agent may quote them.
- Say what the number *means*, not just what it is. "Emergency fund covers less than half a month of expenses" is useful. "emergency_fund_months = 0.4" is not.

**Why this is worth the hour it costs:** it is a literal phrase from the problem statement, it needs no ML, and it gives the demo a second number that changes per customer. Skipping it means a judge who reads the brief closely can ask "where is risk taking ability?" and the honest answer would be that we measured appetite instead.

---

## 3. Revealed Risk Engine ⭐

This module is split in two because it is the differentiator and it has a natural seam.

**3a — Feature extraction · Owner: Saurabh** · **In:** customer record + Profile Engine output · **Out:** the `features_used` object below. Deterministic Python, no ML. This is a standalone module (`features.py`) that anyone can test.

**The six features, defined exactly — settled 27 Aug.** Until now two of them existed only as a number in the example below. `expense_volatility` had no definition anywhere in this document. `budget_overshoot_rate` did have one, but it was buried in the evidence sentence at the end of this section, written for a human to read rather than for an engineer to implement.

| feature | definition | C001 |
|---|---|---|
| `panic_sell_count` | count of `investment_events` where `action == "sell"` **and `days_after_drop` is not null**. A sell in a calm market is not a panic sell. | 2 |
| `avg_days_to_exit_after_drop` | `round(mean(days_after_drop), 1)` over **exactly the events counted above**, so the two features always describe the same population. `null` when `panic_sell_count` is 0 — never `0.0`, which would read as the fastest possible panic. §3b imputes it with the training-set median. | 3.0 |
| `expense_volatility` | `round(statistics.stdev(monthly_totals) / mean(monthly_totals), 2)` over the last 12 monthly expense totals. Sample standard deviation, `n-1`, **not** population. | 0.34 |
| `emergency_fund_months` | **copied from §2's output**, never recomputed. This is the reason §3a takes the profile as well as the record. | 0.4 |
| `equity_allocation_pct` | `round(assets.equity_mf / total_assets, 4)` | 0.5 |
| `budget_overshoot_rate` | `round(share of the last 12 months whose total expense exceeded the 12-month mean, 2)`. Strictly greater than, not `>=`. | 0.42 |

**`panic_sell_count` changed meaning today.** `tools/verify_mocks.py` counted every sell. Both of C001's sells follow drops, so the old and new definitions both give 2 and both pass — they diverge the first time §1 generates a customer who sells in a calm market. `verify_mocks.py` has been tightened to match this table. Do not implement the loose version.

**Two of the six cannot be reproduced from `mocks/customer_C001.json`.** It carries one representative month, and `expense_volatility` and `budget_overshoot_rate` both need twelve. Test those two against a small hand-built fixture with a known mean and standard deviation. A test that claims full equality with `features_out.json` starting from the mock record is a test that lies.

**3b — Model training + prediction · Owner: Shlok** · **In:** `features_used` + `ground_truth_risk` labels · **Out:** `revealed_risk`, `confidence`, `mismatch`, `evidence`, `model_version`.

**Combined output of §3:**

```json
{
  "stated_risk": "aggressive",
  "revealed_risk": "moderate",
  "confidence": 0.82,
  "mismatch": true,
  "features_used": {
    "panic_sell_count": 2,
    "avg_days_to_exit_after_drop": 3.0,
    "expense_volatility": 0.34,
    "emergency_fund_months": 0.4,
    "equity_allocation_pct": 0.50,
    "budget_overshoot_rate": 0.42
  },
  "evidence": [
    "Exited equity MF within 3 days of a 9% market drop (Mar 2024)",
    "Emergency fund covers less than half a month of expenses",
    "Monthly spending overshoots its own 12-month average 42% of the time"
  ],
  "model_version": "rr-v1"
}
```

- `mismatch = (stated_risk != revealed_risk)`
- `evidence` must be **plain readable sentences** — the Challenger Agent quotes these directly, so write them as human sentences, not codes.
- `confidence` is the model's predicted-class probability.
- **Seam rule:** 3a must never import the model and 3b must never touch a raw customer record. 3a delivers a feature vector; 3b delivers a prediction. That way both halves can be built at the same time.
- **Field naming (v1.1 note):** this module's standalone output uses `stated_risk` / `revealed_risk`. §7 and §11 use `risk.stated` / `risk.revealed`. That is intentional — §7 was frozen first and is already being built against. The orchestrator renames once. Do not change either side.
- **`risk_capacity` does not belong here.** It comes from §2 and it is arithmetic, not a prediction. Three separate ideas travel side by side to the frontend and must never be collapsed into one: what they *say* (`stated`), what their behaviour *shows* (`revealed`), and what their finances can *withstand* (`risk_capacity`).

---

## 4. Plan Generator

**Owner: Pushkar** · **In:** Profile output + Risk output + goals + assumptions file · **Out:**

```json
{
  "plans": [
    {
      "plan_id": "A",
      "label": "Steady",
      "monthly_investment": 35000,
      "allocation": { "equity": 0.40, "debt": 0.60 },
      "expected_annual_return": 0.09,
      "projected_corpus": 2660000,
      "goal_amount": 2500000,
      "years": 5,
      "shortfall": 0,
      "feasible": true,
      "surplus_after_investment": 10000
    },
    {
      "plan_id": "B",
      "label": "Balanced",
      "monthly_investment": 30000,
      "allocation": { "equity": 0.65, "debt": 0.35 },
      "expected_annual_return": 0.11,
      "projected_corpus": 2410000,
      "goal_amount": 2500000,
      "years": 5,
      "shortfall": 0,
      "feasible": true,
      "surplus_after_investment": 15000
    }
  ],
  "assumptions_version": "assump-v1"
}
```

- `surplus_after_investment = monthly_surplus - monthly_investment` (**new in v1.1**). Negative when the plan is not affordable. It exists because the Explanation Agent needs to say "this leaves you 10,000 of breathing room" and **the agent is not allowed to do that subtraction itself** — see the note at the end of §7.
- `projected_corpus` is a **SIP annuity-due** total: `monthly_investment * (((1 + r)**n - 1) / r) * (1 + r)` where `r = expected_annual_return / 12` and `n = years * 12`, then **rounded to the nearest 10,000**. The trailing `* (1 + r)` is there because a SIP debits at the *start* of the month, so every instalment earns one extra month of growth; leaving it off understates a five-year plan by roughly 20,000. The rounding is deliberate - a five-year projection has no business claiming rupee precision - and it keeps the number identical on every machine. This was undefined until 27 Aug, and two of the three plan corpus figures in the mocks were hand-written and wrong as a result.
- Generate **2 or 3 plans** — the brief says "couple of plans". Not ten.
- `feasible: false` and a positive `shortfall` if `monthly_investment > monthly_surplus`. Never silently propose a plan the customer cannot afford.
- **All return assumptions live in one file, `assumptions.json`** — nothing hardcoded in the logic. One person owns financial correctness here.

### How the plan is made personal — new in v1.1

The mentor's point was that the plan must follow the user: age, risk taking ability, and context. Three concrete rules, all deterministic:

**1. Allocation ceiling = the more conservative of `risk_capacity` (§2) and `risk.revealed` (§3).**

Not the stated level, and not the higher of the two. If capacity says moderate and behaviour says aggressive, the ceiling is moderate. If capacity says aggressive and behaviour says conservative, the ceiling is conservative.

The one-line version for the demo: *we take the lower of what you can afford to lose and what your history shows you can actually hold.* That sentence is worth rehearsing — it explains the entire risk half of the project in fifteen words.

One plan may deliberately sit **above** the ceiling, so the customer can see the aggressive option and the Verifier can flag it and the Challenger can argue against it. That is the demo, not a bug. But it must be flagged, never quietly recommended.

**2. Age sets the equity band.** Equity share falls as age rises, because a 28-year-old has thirty more earning years to recover a bad decade and a 55-year-old does not. Put the bands in `assumptions.json`, not in the code, so the number is visible and arguable rather than buried.

**3. Horizon overrides age.** A three-year goal is a short-horizon goal whether the customer is 25 or 55, because there is not enough time to recover a bad year. When horizon and age disagree, horizon wins.

Every one of these three is a line of arithmetic, and every one of them makes a visible difference on screen between two customers. That is the difference between a plan that is *for* someone and a plan with their name printed at the top.

---

## 5. Monte Carlo Simulation

**Owner: Pushkar** · **In:** plans + historical returns CSV · **Out:**

```json
{
  "n_simulations": 10000,
  "results": [
    {
      "plan_id": "A",
      "success_probability": 0.87,
      "successful_simulations": 8700,
      "median_corpus": 2680000,
      "p10_corpus": 2150000,
      "p90_corpus": 3320000,
      "p10_gap_to_goal": 350000
    }
  ],
  "returns_data_source": "nifty_yearly_2005_2025.csv"
}
```

- **`returns_data_source` is mandatory.** Returns must be sampled from a real historical dataset, not a hardcoded average. This is what satisfies the brief's *"using past trend data"* clause — do not skip it.
- `success_probability` = fraction of simulations where final corpus ≥ `goal_amount`.
- `successful_simulations` = the raw count (**new in v1.1**). "8,700 out of 10,000 simulations reached your goal" lands far harder on a listener than "87%", and the agent is not permitted to multiply 0.87 by 10,000 itself.
- `p10_gap_to_goal = max(0, goal_amount - p10_corpus)` (**new in v1.1**). The size of the miss in the bad outcomes. Same reason: the agent may not subtract.
- Sample by **resampling actual historical annual returns with replacement**, not from a normal distribution. Real returns have fatter tails than a bell curve, so a normal distribution quietly overstates the success probability. Resampling also captures **sequence risk** — the same average return gives a different answer depending on whether the bad years land early or late. If a judge asks one hard question about the simulation, it will be this one.

---

## 6. Stress Test ⭐

**Owner: Pushkar** · **In:** plans + shock event library · **Out:**

```json
{
  "results": [
    {
      "plan_id": "A",
      "survives": true,
      "breaking_combo": null,
      "breaking_probability": null,
      "shortfall_if_hit": null,
      "combos_tested": 165
    },
    {
      "plan_id": "B",
      "survives": false,
      "breaking_combo": [
        { "event_id": "appraisal_miss",  "label": "Appraisal comes in at 4% instead of 10%", "annual_probability": 0.23, "cash_impact": -180000 },
        { "event_id": "medical_expense", "label": "Family medical expense",                  "annual_probability": 0.10, "cash_impact": -200000 }
      ],
      "breaking_probability": 0.023,
      "shortfall_if_hit": 420000,
      "combos_tested": 165
    }
  ]
}
```

### Shock event library (`shocks.json`, also Pushkar)

```json
[
  { "event_id": "job_loss_3m", "label": "Job loss for 3 months",
    "annual_probability": 0.04, "cash_impact": -360000 }
]
```

- ~10 events. Brute-force all 2- and 3-event combinations (~165) and report the **cheapest combination that makes the plan fail**.
- `breaking_probability` = product of the individual event probabilities (state this assumption openly — events are treated as independent, which is a simplification). In the example above that is `0.23 × 0.10 = 0.023`. **v1.2 fixed this example** — it previously read `0.11`, which contradicted this very rule, and the shock probabilities were not shown so nobody could catch it.
- **Copy each shock straight out of `shocks.json`, `annual_probability` included** (**v1.2**). The UI shows how likely each individual shock is, and the Verifier needs those digits in its whitelist — otherwise the agent gets failed for quoting a probability we gave it.
- `combos_tested` (**new in v1.2**) is how many combinations you actually evaluated. One integer, and "165 combinations tested" is a good line on screen.
- **Naming seam, do not fix it:** this module outputs `survives`. §7 and §11 both use `survives_stress`. The orchestrator renames it exactly once, in `merge_plans`. This is the same kind of deliberate seam as §3's `revealed_risk` → `risk.revealed`. Renaming it at either end breaks the other end.

---

## 7. Orchestrator → Agent payload (`plan_bundle`) 🔒

**Owner: Shlok** · This is the **de-identified** object handed to every agent. Note what is absent: no name, no `customer_id`, no account numbers.

```json
{
  "context": {
    "age": 28,
    "dependents": 1,
    "employment_type": "salaried",
    "city_tier": "metro"
  },
  "profile": {
    "net_worth": 600000,
    "monthly_income": 120000,
    "monthly_expense": 75000,
    "monthly_surplus": 45000,
    "emergency_fund_months": 0.4,
    "risk_capacity": "moderate",
    "risk_capacity_reasons": [
      "Monthly surplus of 37% of income is healthy",
      "Emergency fund covers less than half a month of expenses"
    ]
  },
  "risk": {
    "stated": "aggressive",
    "revealed": "moderate",
    "confidence": 0.82,
    "mismatch": true,
    "panic_sell_count": 2,
    "evidence": ["Exited equity MF within 3 days of a 9% market drop (Mar 2024)"]
  },
  "goals": [
    { "name": "house_downpayment", "target_amount": 2500000, "years": 5, "priority": 1 }
  ],
  "plans": [
    {
      "plan_id": "A",
      "label": "Steady",
      "monthly_investment": 35000,
      "surplus_after_investment": 10000,
      "allocation": { "equity": 0.40, "debt": 0.60 },
      "projected_corpus": 2660000,
      "goal_amount": 2500000,
      "years": 5,
      "feasible": true,
      "shortfall": 0,
      "success_probability": 0.87,
      "successful_simulations": 8700,
      "median_corpus": 2680000,
      "p10_corpus": 2150000,
      "p90_corpus": 3320000,
      "p10_gap_to_goal": 350000,
      "survives_stress": true,
      "breaking_combo": null,
      "breaking_probability": null,
      "shortfall_if_hit": null,
      "exceeds_risk_ceiling": false
    }
  ],
  "comparisons": {
    "cheapest_plan_id": "B",
    "highest_success_plan_id": "A",
    "plan_count": 3,
    "monthly_investment_delta_vs_cheapest": { "A": 5000, "B": 0, "C": 22000 }
  },
  "n_simulations": 10000
}
```

The Orchestrator merges Plan Generator + Monte Carlo + Stress Test per `plan_id` into one flat plan object, so agents never have to join data themselves.

### What the Orchestrator does to build this — new in v1.2

Three transformations, all in `orchestrator/pipeline.py`, none of them arithmetic on engine output:

- **Renames two fields, once each.** §3's `stated_risk` / `revealed_risk` become `risk.stated` / `risk.revealed`, and §6's `survives` becomes `survives_stress`. Both seams are deliberate. Neither engine changes.
- **Drops what the agents do not need.** `expected_annual_return` (§4) and `combos_tested` (§6) are in §11 but not here. `profile` is trimmed to seven fields and `risk` to six. Less in the payload means less for an agent to misread.
- **Adds `panic_sell_count`** from §3a's features, and computes `comparisons`. These are the only two numbers in this payload the orchestrator produces rather than passes through, and both exist because an agent would otherwise have to count or subtract.

`panic_sell_count` is here so the Challenger can say "you sold during a drop on two occasions" without counting the `evidence` array itself. **Counting is arithmetic.** The rule below has no exception for small numbers.

### What is in this payload and what is not

**Not here:** name, `customer_id`, account numbers, `ground_truth_risk`. Those are identifiers and answer keys, and the LLM never sees them. The name is added back in §11, after the agents have finished.

**Here, and deliberately so:** age, dependents, employment type, city tier. These are *attributes*, not identifiers — they cannot pick a person out of a crowd, and without them the agent cannot write a sentence that reflects who the customer is. If a judge asks about privacy, that distinction is the answer: we removed everything that identifies and kept everything that describes.

### The rule that made this payload bigger — read this even if you skim the rest ⭐

An agent may not perform arithmetic. Not addition, not subtraction, not multiplication, not rounding, not percent-to-count conversion. **Every number in the prose must already exist, exactly, somewhere in this payload.**

That sounds obvious and it is easy to break by accident. Draft explanation text usually contains sentences like "leaves you 10,000 of breathing room", "8,700 out of 10,000 simulations", "falls 7,20,000 short of target", "needs 5,000 more per month than the other plan". Every one of those reads as a fact and every one of them is a calculation the agent did on its own. Our own Verifier would fail all four, correctly, and the retry would fail again for the same reason.

So the fix is not to relax the Verifier. **The fix is that the engines pre-compute every derived number the prose is going to want.** That is where `surplus_after_investment`, `successful_simulations`, `p10_gap_to_goal` and `comparisons` come from — each one exists because a sentence we want to say needs it.

If you are writing agent prompts and you find yourself wanting a number that is not in this payload, the answer is never "let the model work it out". Ask for the field in the group and it gets added to the engine that owns it.

---

## 8. Explanation Agent

**Owner: Madhura** · **In:** `plan_bundle` (§7) · **Out:**

```json
{
  "plans_text": [
    {
      "plan_id": "A",
      "headline": "Invest ₹35,000 a month, mostly in debt",
      "body": "This plan puts 40% in equity and 60% in debt...",
      "pros": ["Highest chance of reaching your goal", "Survives our stress test"],
      "cons": ["Needs ₹5,000 more per month than Plan B"]
    }
  ],
  "goal_priority_note": "Your house goal is funded first because...",
  "mismatch_note": "You described yourself as aggressive, but your past behaviour looks moderate.",
  "numbers_used": [35000, 2660000, 0.87, 2500000, 5, 0.40, 0.60]
}
```

### Hard rules for this agent

- **`numbers_used` is mandatory.** The agent must declare every number it used. This is what makes the Verifier reliable instead of guessing with regex.
- Every number in `numbers_used` must exist in `plan_bundle`. Do not compute, round, convert, or infer new figures.
- `goal_priority_note` is where GenAI does genuine **customisation** — deciding goal ordering and trade-off framing when goals conflict. This is what makes GenAI more than a narrator, and it matters for brief compliance.

---

## 9. Verifier Agent ⭐

**Owner: Pushkar** · **In:** Explanation output (§8) + `plan_bundle` (§7) · **Out:**

```json
{
  "status": "fail",
  "numbers_checked": 34,
  "unverified_numbers": [36000],
  "suitability_flags": [
    "Plan C equity allocation 0.85 exceeds revealed risk level 'moderate'"
  ],
  "retry_count": 1
}
```

### How it checks

1. Every value in `numbers_used` must be findable in `plan_bundle`.
2. **Also** regex-sweep the prose for numbers as a backup, in case the agent under-declared.
3. **Normalise before comparing** — `"₹35,000"`, `"35000"`, `"35,000"`, `"₹35k"` are the same number. Skipping this causes false failures. Two more rules, **added in v1.2, both of which cause false failures rather than false passes**:
   - **Indian digit grouping.** `"26,20,000"` is `2620000`. A regex written for western commas reads it as `2620`, fails to find it, and then reports every money figure in the prose as invented. Strip commas before parsing; do not assume groups of three.
   - **Percentages read two ways.** `"40%"` may legitimately be a stored `0.4` or a stored `40` — allocations are fractions, percentiles are not. Offer both candidates and pass if either is in the whitelist.
4. **Build the whitelist from engine-written strings too, not only numeric fields** (**v1.2**). The Challenger quotes `evidence` verbatim, and that prose contains digits: "Exited equity MF within 3 days of a 9% market drop (Mar 2024)" contributes `3`, `9` and `2024`. Miss this and the agent gets failed for quoting us accurately, which is the most demoralising possible false positive.
5. **Check 5 — forbidden phrases, matched on words rather than digits** (**new in v1.2, and the most important addition to this section**). See below.
6. Suitability: flag if a recommended allocation is more aggressive than the **lower of `risk.revealed` and `risk_capacity`** permits. Both, not just one — a plan can be wrong because the customer will not hold it, or wrong because they cannot afford to lose it, and those are separate failures.

### Check 5, and why the first four are not enough ⭐

A whitelist confirms a number **exists** in engine output. It cannot confirm the number **means** what the sentence claims. That gap is real and it was found by planting deliberate errors, not by reasoning about the design.

The sentence that proves it:

> "There is a 71% chance you abandon this plan within seven weeks."

That passes every numeric check, because `0.71` genuinely is plan B's `success_probability`. A real number has been bolted onto a quantity nothing in this pipeline measures. **No amount of whitelist strictness catches it** — the number is not invented, the meaning is.

It is catchable for one specific reason: we cut the ML adherence model, so **nothing anywhere in this system predicts human behaviour.** Every engine measures money or market outcomes. So any probability attached to a person's future *action* is invented by construction, and can be rejected on its wording without knowing anything about the numbers.

Reject prose matching any of these:

| Pattern | Why |
|---|---|
| "chance / probability / odds / likelihood … you" | a probability about the customer's own behaviour |
| "you will abandon / quit / give up / stop investing / panic" | a prediction about what the customer will do |
| a percentage in the same sentence as a behaviour verb | the disguised version of the two above |
| "guarantee", "guaranteed" | a guarantee about an uncertain outcome |
| "will definitely", "is certain to", "cannot fail" | certainty we do not have |
| "recommend buying", "you should sell" | a specific product instruction, which is regulated advice |

**Known remaining hole, stated honestly because a judge may find it:** numbers written as words — "twenty years", "two occasions", "five years" — escape a digit regex entirely. They are covered only by check 1, the agent declaring them in `numbers_used`. That hole is exactly what let the phrase "twenty years of historical market returns" sit in a committed mock unnoticed, describing a dataset length no field states. If you have spare time, a word-to-digit pass for zero through twenty and the round hundreds/thousands closes most of it.

- `numbers_checked` is the count of numbers actually verified (**new in v1.1**). Put it on the screen. "34 numbers checked, 0 unverified" is the single most convincing thing in the demo for a banking audience, and it costs one variable.
- `status: "fail"` → send back to the Explanation Agent to regenerate. **Max 2 retries**, then fall back to a plain template rendering of the numbers.
- **This module is plain Python. It is not an LLM.** Regex extraction plus a whitelist comparison against engine output. An LLM asked to check another LLM can hallucinate agreement, which would leave us with a check that reports success and verifies nothing — worse than having no check at all, because we would trust it.
- **Plant known-bad numbers in your own test and prove it fails.** A verifier that passes everything is indistinguishable from a verifier that does nothing, and you cannot tell which one you built by watching it pass. `tools/verify_mocks.py` on `main` is a working reference implementation of everything in this section, self-test included — read it before writing your own.

---

## 10. Challenger Agent

**Owner: Madhura** · **In:** `plan_bundle` + `chosen_plan_id` · **Out:**

```json
{
  "chosen_plan_id": "C",
  "challenge": "Plan C asks for the smallest monthly amount, but your history shows you exited equity within 3 days of a 9% drop...",
  "evidence_cited": ["Exited equity MF within 3 days of a 9% market drop (Mar 2024)"],
  "alternative_suggested": "A"
}
```

### ⚠️ Hard rule

**No invented numbers. Especially no made-up probabilities.** We cut the ML adherence model, so this agent must **never** say things like "you will abandon this in 7 weeks with 71% probability" — that number does not exist anywhere, our own Verifier would fail it, and it destroys the credibility the whole project is built on.

Argue **qualitatively from `evidence`** instead. "Your history shows you sell during drops" is evidence-based and strong. A fabricated percentage is fatal.

---

## 11. Final API response → Frontend 🔒

**Owner: Shlok** (moved from the frontend group in the 26 Aug restructure) · The backend adds the name back here — *after* the agents have run.

> **The committed file `mocks/api_response.json` on `main` is the authority for this section.** It is a complete, valid, hand-written example with three plans covering every state the UI has to render. Build against the file, not against this description. If the two ever disagree, the file is right and this document gets fixed.

### Top-level keys

```json
{
  "schema_version": "api-v1",
  "customer_id": "C001",
  "customer_name": "Rahul Mehta",
  "generated_at": "2026-08-25",
  "context":            { "...": "age, dependents, employment_type, city_tier" },
  "profile":            { "...": "§2 output, in full, including risk_capacity" },
  "risk":               { "...": "§3 output, renamed to stated / revealed" },
  "goals":              [ "...as submitted, with priority" ],
  "plans":              [ "...see the plan object below" ],
  "goal_priority_note": "§8",
  "mismatch_note":      "§8",
  "peer_cohort":        { "...": "§16, or null" },
  "challenge":          null,
  "verifier":           { "...": "§9 output" },
  "meta":               { "...": "provenance, see below" }
}
```

- `customer_id` is **required** (fixed in v1.1). Without it the frontend cannot call `/api/challenge` or `/api/whatif`, both of which need it in the request body.
- `generated_at` is a **date**, `"2026-08-26"`, not a timestamp (**pinned in v1.2** — the committed mock has always been a date).
- `challenge` is `null` on the first response and only populated after the customer picks a plan.
- `peer_cohort` may be `null` — the frontend must hide that section rather than break.
- `meta` carries provenance: `returns_data_source`, `n_simulations`, `assumptions_version`, `model_version`. It exists so the demo can answer "where did this number come from" on screen instead of verbally.

### The plan object — the correction in v1.1

v1.0 described this as "§7 merged with §8". That was wrong: §7 is the trimmed, de-identified agent payload, and a UI built on it could not show affordability, the range of outcomes, or the odds of the breaking combination. **The plan object here is the full merge of §4 + §5 + §6 + §8, keyed by `plan_id`.**

| Field | From | Notes |
|---|---|---|
| `plan_id`, `label` | §4 | |
| `monthly_investment` | §4 | |
| `surplus_after_investment` | §4 | negative when unaffordable |
| `allocation` | §4 | fractions summing to 1.0 |
| `expected_annual_return` | §4 | |
| `projected_corpus` | §4 | |
| `goal_amount`, `years` | §4 | needed to render "X against your Y target in Z years" |
| `shortfall`, `feasible` | §4 | drives the "not affordable" state |
| `success_probability` | §5 | |
| `successful_simulations` | §5 | |
| `median_corpus`, `p10_corpus`, `p90_corpus` | §5 | the outcome range |
| `p10_gap_to_goal` | §5 | |
| `survives_stress` | §6 | renamed from §6's `survives` by the orchestrator |
| `breaking_combo` | §6 | `null` when it survives. Each shock carries `annual_probability` (**v1.2**) |
| `breaking_probability`, `shortfall_if_hit` | §6 | `null` when it survives |
| `exceeds_risk_ceiling` | §4 | `true` for the deliberately over-aggressive plan |
| `headline`, `body`, `pros`, `cons` | §8 | the only LLM-written fields in the object |

**Every field in that table is either engine output or agent prose. Nothing is computed here.** The API layer joins and returns; it does not calculate. The moment it calculates, there are two places numbers come from and the audit story breaks.

---

## 12. API endpoints

**Owner: Shlok** (moved in the 26 Aug restructure)

| Method | Path | Body | Returns |
|---|---|---|---|
| `POST` | `/api/plan` | customer form (below) or `{"customer_id": "C001"}` | §11 |
| `POST` | `/api/challenge` | `{"customer_id": "C001", "chosen_plan_id": "C"}` | §10 |
| `POST` | `/api/whatif` | `{"customer_id": "C001", "extra_monthly_savings": 10000}` | §11 recomputed |
| `GET` | `/api/status` | — | which stages are real engines and which are still mocks (**new in v1.2**) |

Frontend form body for `/api/plan`:

```json
{
  "age": 28,
  "dependents": 1,
  "employment_type": "salaried",
  "city_tier": "metro",
  "monthly_income": 120000,
  "monthly_expense": 75000,
  "assets": 800000,
  "liabilities": 200000,
  "savings_account": 30000,
  "stated_risk": "aggressive",
  "goals": [
    { "name": "house_downpayment", "target_amount": 2500000, "years": 5, "priority": 1 }
  ]
}
```

- `dependents`, `employment_type` and `city_tier` are **new in v1.1** and required, because `risk_capacity` cannot be computed without them.
- `savings_account` is required and separate from `assets`, because `emergency_fund_months` uses only the liquid part. Total assets alone cannot tell us whether the customer can reach any of it in a week.
- `monthly_expense` is accepted directly from the form. For a form-submitted customer there is no transaction history, so §3's behavioural features are unavailable — in that case `risk.revealed` is `null`, `mismatch` is `false`, and the frontend shows stated risk and `risk_capacity` only. **This is the one path where the differentiator cannot run, and it must degrade cleanly rather than crash.** The demo uses a pinned persona precisely so that it does not hit this path.
- **Rules:** three endpoints, no business logic, roughly sixty lines. The endpoint calls the pipeline and returns the dictionary. Errors from engines are Python exceptions; the API converts them to a status code and a message.
- **How `/api/whatif` works** (**v1.2**): the orchestrator adds `extra_monthly_savings` to `profile.monthly_surplus` and re-runs the same pipeline. It is not a second code path, and **§4's signature does not change** — the plan generator simply sees a larger surplus, which is literally what the question asks. Caveat while §4 is still a mock: the surplus in the response moves and the plan numbers do not, so this endpoint must not be demoed until §4 is real.
- **`GET /api/status`** (**v1.2**) returns each stage as `"engine"` or `"mock"`, plus a count. It exists so nobody has to ask in the group chat what is finished, and so the demo can state out loud which numbers are computed instead of being asked and guessing.
- CORS must be enabled for the frontend's dev server origin, or every request fails in the browser with an error that looks like a backend bug and is not one. Cost of forgetting: an hour of confusion on integration day.

---

## 13. Mock files — every one of these on `main` today

So nobody is ever blocked, and so the demo has a fallback if a module breaks:

```
/mocks
  customer_C001.json      → §1   (Saurabh)
  profile_out.json        → §2   (Saurabh)
  features_out.json       → §3a  (Saurabh)
  risk_out.json           → §3   (Shlok)
  plans_out.json          → §4   (Pushkar)
  montecarlo_out.json     → §5   (Pushkar)
  stress_out.json         → §6   (Pushkar)
  plan_bundle.json        → §7   (Shlok)
  explanation_out.json    → §8   (Madhura)
  peer_cohort_out.json    → §16  (Shlok)
  api_response.json       → §11  (Shlok) ✅ committed 25 Aug
```

**Write these by hand, with realistic values, before writing any engine code.** They are not throwaway. Three things depend on them:

1. **Nobody is blocked.** The frontend group builds the entire UI against `api_response.json`. The agent prompts are written against `plan_bundle.json`. Neither has to wait for a single engine.
2. **The pipeline runs today.** The orchestrator reads mocks, joins them, and produces a §11 response with zero real engines behind it. Each engine then replaces its own mock one at a time, and the pipeline never stops working in between. That is why integration happens on day one instead of on the 29th.
3. **They are the demo safety net.** If an engine breaks an hour before the demo, its mock goes back in and the demo still runs.

**Values must be internally consistent.** Net worth equals assets minus liabilities, surplus equals income minus expense, the expense breakdown sums to the total, allocations sum to 1.0. A mock with numbers that do not add up teaches everyone the wrong shape and produces a demo a judge can break with mental arithmetic.

---

## 14. Ownership — rewritten 26 Aug 2026

There is **no team leader**. Ownership is per-module and every module has exactly one name that answers for it.

The team is split into two groups by physical location. **The frontend group of four owns the entire interface** and chooses its own frontend technology; they work remotely. **The compute group of four owns everything else** and can meet in person.

### Frontend group

| Area | Owner |
|---|---|
| UI/UX, all screens, all states | Supriya, Hemant, Tiya, Varada — divided among themselves |
| Deck visuals and screen design | same group |

Their single source of truth is `UI_REQUIREMENTS.md` plus this contract. They build against `mocks/api_response.json` and never against a live backend until integration.

### Compute group

| § | Module | Owner |
|---|---|---|
| 1 | Synthetic Data Generator | Saurabh |
| 2 | Profile Engine + `risk_capacity` | Saurabh |
| 3a | Feature extraction (`features.py`) | Saurabh |
| — | `nifty_yearly_2005_2025.csv`, `assumptions.json` (the numbers) | Saurabh |
| 3b | Revealed Risk model training ⭐ | Shlok |
| 4 | Plan Generator (the code that reads `assumptions.json`) | Pushkar |
| 5 | Monte Carlo | Pushkar |
| 6 | Stress Test + `shocks.json` ⭐ | Pushkar |
| 9 | Verifier Agent ⭐ | Pushkar |
| 7 | Orchestrator + `plan_bundle` | Shlok |
| 11–12 | API layer | Shlok |
| 16 | Peer Cohort Engine | Shlok |
| — | Integration, branch merges, this contract | Shlok |
| 8 | Explanation Agent | Madhura |
| 10 | Challenger Agent | Madhura |
| — | Pitch narrative, demo script, deck content | Madhura |

### Two deliberate choices in that table

**§1 goes to the person whose own work it unblocks.** Whoever builds the profile engine and the feature extractor needs customer records first. Giving all three to one person removes a handoff that would otherwise happen twice.

**The Verifier is owned by someone other than the author of the Explanation Agent.** The Verifier exists to catch the Explanation Agent inventing numbers. One person marking their own work would quietly weaken the one check the project is built on.

**One seam to respect:** the returns CSV and `assumptions.json` are owned by one person as *files and numbers*; the code that reads them is owned by another. Nobody edits the other's side. This is the only file both groups touch, so it is the only place a silent conflict can happen.

### Rules instead of a leader

- **Feature freeze: 29 Aug.** Agreed by everyone in writing on Day 1, so it is the group's rule and not a person's order.
- **Contract changes go to the group first**, never silently.
- **Stuck for 3+ hours → say it in the group.** No exceptions.
- **Nobody pushes to `main`.** One branch per person, pull request, merged each evening.
- **Shared files are add-only**: this contract, `requirements.txt`, `README.md`, `.gitignore`. Need a package? Post in the group and it is added in one commit.
- **Escalation trigger, agreed in advance:** if §1, §2, §3a, §4 and §5 are not done by the end of 27 Aug, one person comes back from the frontend group. Deciding this now, while nobody is behind, means it is a plan rather than an accusation later.
- **First thing cut if time runs short: §16, the peer cohort.** It is a mentor suggestion, not a requirement in the brief. Everything else is load-bearing. Knowing what to cut before we need to cut it is the difference between de-scoping and panicking.

---

## 15. What must be true by tonight — 26 Aug

1. **All ten remaining mock files in `/mocks`, committed, with consistent values.** Roughly fifteen minutes each. Until these exist, people are blocked on each other for no reason.
2. **The orchestrator runs end to end on nothing but mocks** and prints a valid §11 response. Zero real engines. This is mostly dictionary joining, and once it works the project is never in a non-working state again.
3. **The synthetic data generator produces one valid `C001` record** that matches §1 exactly. One record, not a thousand — the thousand is a loop afterwards. One valid record proves the schema.

Nothing else matters today.

---

## 16. Peer Cohort Engine — new in v1.1

**Owner: Shlok** · **In:** the full generated customer dataset (§1) + this customer's §2 profile and §3 risk output · **Out:**

```json
{
  "cohort_size": 87,
  "matched_on": ["age_band", "income_band", "goal_type", "stated_risk"],
  "age_band": "26-30",
  "income_band": "100000-150000",
  "goal_type": "house_downpayment",
  "median_monthly_surplus": 38000,
  "median_savings_rate": 0.32,
  "customer_savings_rate": 0.375,
  "savings_rate_percentile": 68,
  "mismatch_rate": 0.61,
  "most_common_plan_label": "Balanced",
  "most_common_allocation": { "equity": 0.6, "debt": 0.4 }
}
```

This is the mentor's "look for customers with the same profile". It is the reason we generate a thousand records instead of three: with a dataset that size, a cohort is a real query rather than a claim.

### Bands

- `age_band`: `22-25`, `26-30`, `31-35`, `36-40`, `41-50`, `51+`
- `income_band`: `0-50000`, `50000-100000`, `100000-150000`, `150000-250000`, `250000+`
- `goal_type`: the `name` of the customer's priority-1 goal
- `stated_risk`: the enum from §0

### Matching rule, with a fallback that must not be skipped

Match on all four keys. If fewer than **20** customers match, drop the least important key and try again, in this order: `stated_risk` first, then `goal_type`. Record what you actually matched on in `matched_on`, so the screen can say "87 customers in your age and income band" honestly instead of implying a tighter match than we made.

If still fewer than 20 after both fallbacks, **return `null`**. The frontend hides the section. A cohort of four is not a cohort, and a percentile computed from four people is a number with no meaning that a judge can dismantle in one question.

### Privacy rule 🔒

**Aggregates only, minimum cohort size 20, and never an individual peer** — no ID, no row, no "a customer like you did X". This is not a formality. Cohort comparison is a feature banks genuinely want and genuinely cannot ship if it leaks, and being able to say "we compare you to a group and the group is never small enough to identify anyone in it" turns a privacy question from a weakness into an answer we prepared.

### Fields worth understanding before you build it

- `savings_rate = monthly_surplus / monthly_income`. `customer_savings_rate` is this customer's; `median_savings_rate` is the cohort's.
- `savings_rate_percentile` is where this customer sits in the cohort, 0 to 100. This is the one number people react to emotionally, so it is the one to put on screen largest.
- `mismatch_rate` is the fraction of the cohort whose stated risk differs from their revealed risk. **This is quietly the strongest number in the project.** "61% of people like you also describe themselves as more aggressive than their behaviour suggests" turns our differentiator from a claim about one customer into a claim about a population — which is the difference between a feature and a finding.
- `most_common_plan_label` and `most_common_allocation` are what the cohort chose. Show them as context, never as a recommendation. What most people picked is not evidence that it was right for them, and presenting it as advice would be the one dishonest number on the screen.
