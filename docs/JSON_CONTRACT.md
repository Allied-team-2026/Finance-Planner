# JSON Data Contract — Finance Planning (Cognizant Hackathon)

**Version 1.0 · Frozen 24 Aug 2026 · Owner: Shlok**

This document defines exactly what every module takes in and gives out. Once frozen, **nobody waits for anybody** — build against the mock data and it will fit on integration day.

> **Rule:** If you need to change a field, message the group first. Do not change it silently. A renamed field on Day 4 costs the whole team hours.

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
| Plan IDs | Single uppercase letter | `"A"`, `"B"`, `"C"` |
| Missing value | `null`, never `0` or `""` | `"breaking_combo": null` |
| Errors | Raise a Python exception; the API layer converts it. Engines never return error strings. | — |

**Privacy rule (non-negotiable):** No PII ever goes to the LLM. No name, no `customer_id`, no account number. Agents receive only numbers and categories. The name is added back by the backend *after* the agents run. See §7.

---

## 1. Synthetic Data Generator → customer record

**Owner: Tiya** (schema co-designed with Varada)

Produces **~1000+ customer records** for model training, plus **3 fixed demo personas** (`C001`, `C002`, `C003`).

Transactions must span **at least 24 months** so there is real "past trend data".

```json
{
  "customer_id": "C001",
  "age": 28,
  "stated_risk": "aggressive",
  "monthly_income": 120000,
  "assets": {
    "savings_account": 300000,
    "equity_mf": 400000,
    "fixed_deposit": 100000
  },
  "liabilities": [
    { "type": "car_loan", "outstanding": 200000, "emi": 8000 }
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

### Critical notes

- `ground_truth_risk` is **for ML training and evaluation only**. It must **never** enter the planning pipeline or reach the frontend. Treat it as a hidden answer key.
- Generate behaviour with **noise and confounders** — do not derive `ground_truth_risk` from a single clean rule, or the ML model just relearns your rule and the whole differentiator collapses under questioning.
- `category` values (fixed list): `rent`, `groceries`, `utilities`, `transport`, `dining`, `shopping`, `health`, `education`, `entertainment`, `emi`, `insurance`, `misc`.

### The 3 demo personas must be

| ID | Purpose |
|---|---|
| `C001` | Stated `aggressive`, revealed `moderate` → **mismatch** (shows differentiator 1) |
| `C002` | Stated `moderate`, revealed `moderate` → **match** (proves the model isn't always crying mismatch) |
| `C003` | Plan breaks dramatically under stress test (shows differentiator 2) |

---

## 2. Profile Engine

**Owner: Tiya** · **In:** customer record (§1) or frontend form (§12) · **Out:**

```json
{
  "net_worth": 600000,
  "total_assets": 800000,
  "total_liabilities": 200000,
  "monthly_income": 120000,
  "monthly_expense": 75000,
  "monthly_surplus": 45000,
  "existing_emi_total": 8000,
  "emergency_fund_months": 0.0,
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

---

## 3. Revealed Risk Engine ⭐

This module is split in two because it is the differentiator and it has a natural seam.

**3a — Feature extraction · Owner: Varada** · **In:** customer record + Profile Engine output · **Out:** the `features_used` object below. Deterministic Python, no ML. This is a standalone module (`features.py`) that anyone can test.

**3b — Model training + prediction · Owner: core pod (Shlok + Pushkar + Saurabh)** · **In:** `features_used` + `ground_truth_risk` labels · **Out:** `revealed_risk`, `confidence`, `mismatch`, `evidence`, `model_version`.

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
    "emergency_fund_months": 0.0,
    "equity_allocation_pct": 0.50,
    "budget_overshoot_rate": 0.42
  },
  "evidence": [
    "Exited equity MF within 3 days of a 9% market drop (Mar 2024)",
    "No emergency fund",
    "Monthly spending overshoots its own 12-month average 42% of the time"
  ],
  "model_version": "rr-v1"
}
```

- `mismatch = (stated_risk != revealed_risk)`
- `evidence` must be **plain readable sentences** — the Challenger Agent quotes these directly, so write them as human sentences, not codes.
- `confidence` is the model's predicted-class probability.
- **Seam rule:** 3a must never import the model and 3b must never touch a raw customer record. Varada delivers a feature vector; the pod delivers a prediction. That way both halves can be built at the same time.

---

## 4. Plan Generator

**Owner: Hemant** · **In:** Profile output + Risk output + goals + assumptions file · **Out:**

```json
{
  "plans": [
    {
      "plan_id": "A",
      "label": "Steady",
      "monthly_investment": 35000,
      "allocation": { "equity": 0.40, "debt": 0.60 },
      "expected_annual_return": 0.09,
      "projected_corpus": 2620000,
      "goal_amount": 2500000,
      "years": 5,
      "shortfall": 0,
      "feasible": true
    },
    {
      "plan_id": "B",
      "label": "Balanced",
      "monthly_investment": 30000,
      "allocation": { "equity": 0.65, "debt": 0.35 },
      "expected_annual_return": 0.11,
      "projected_corpus": 2540000,
      "goal_amount": 2500000,
      "years": 5,
      "shortfall": 0,
      "feasible": true
    }
  ],
  "assumptions_version": "assump-v1"
}
```

- Generate **2 or 3 plans** — the brief says "couple of plans". Not ten.
- `feasible: false` and a positive `shortfall` if `monthly_investment > monthly_surplus`. Never silently propose a plan the customer cannot afford.
- **All return assumptions live in one file, `assumptions.json`** — nothing hardcoded in the logic. Hemant owns financial correctness here.

---

## 5. Monte Carlo Simulation

**Owner: Hemant** · **In:** plans + historical returns CSV · **Out:**

```json
{
  "n_simulations": 10000,
  "results": [
    {
      "plan_id": "A",
      "success_probability": 0.87,
      "median_corpus": 2680000,
      "p10_corpus": 2150000,
      "p90_corpus": 3320000
    }
  ],
  "returns_data_source": "nifty_yearly_2005_2025.csv"
}
```

- **`returns_data_source` is mandatory.** Returns must be sampled from a real historical dataset, not a hardcoded average. This is what satisfies the brief's *"using past trend data"* clause — do not skip it.
- `success_probability` = fraction of simulations where final corpus ≥ `goal_amount`.

---

## 6. Stress Test ⭐

**Owner: Pushkar** (with Saurabh) · **In:** plans + shock event library · **Out:**

```json
{
  "results": [
    {
      "plan_id": "A",
      "survives": true,
      "breaking_combo": null,
      "breaking_probability": null,
      "shortfall_if_hit": null
    },
    {
      "plan_id": "C",
      "survives": false,
      "breaking_combo": [
        { "event_id": "appraisal_miss",   "label": "Appraisal comes in at 4% instead of 10%", "cash_impact": -180000 },
        { "event_id": "medical_expense",  "label": "Family medical expense",                  "cash_impact": -200000 }
      ],
      "breaking_probability": 0.11,
      "shortfall_if_hit": 420000
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
- `breaking_probability` = product of the individual event probabilities (state this assumption openly — events are treated as independent, which is a simplification).

---

## 7. Orchestrator → Agent payload (`plan_bundle`) 🔒

**Owner: Shlok** · This is the **de-identified** object handed to every agent. Note what is absent: no name, no `customer_id`, no account numbers.

```json
{
  "profile": {
    "net_worth": 600000,
    "monthly_income": 120000,
    "monthly_surplus": 45000,
    "emergency_fund_months": 0.0
  },
  "risk": {
    "stated": "aggressive",
    "revealed": "moderate",
    "confidence": 0.82,
    "mismatch": true,
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
      "allocation": { "equity": 0.40, "debt": 0.60 },
      "projected_corpus": 2620000,
      "success_probability": 0.87,
      "survives_stress": true,
      "breaking_combo": null
    }
  ]
}
```

The Orchestrator merges Plan Generator + Monte Carlo + Stress Test per `plan_id` into one flat plan object, so agents never have to join data themselves.

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
  "numbers_used": [35000, 2620000, 0.87, 2500000, 5, 0.40, 0.60]
}
```

### Hard rules for this agent

- **`numbers_used` is mandatory.** The agent must declare every number it used. This is what makes the Verifier reliable instead of guessing with regex.
- Every number in `numbers_used` must exist in `plan_bundle`. Do not compute, round, convert, or infer new figures.
- `goal_priority_note` is where GenAI does genuine **customisation** — deciding goal ordering and trade-off framing when goals conflict. This is what makes GenAI more than a narrator, and it matters for brief compliance.

---

## 9. Verifier Agent ⭐

**Owner: Pushkar** (with Shlok) · **In:** Explanation output (§8) + `plan_bundle` (§7) · **Out:**

```json
{
  "status": "fail",
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
3. **Normalise before comparing** — `"₹35,000"`, `"35000"`, `"35,000"`, `"₹35k"` are the same number. Skipping this causes false failures.
4. Suitability: flag if a recommended allocation is more aggressive than `risk.revealed` permits.

- `status: "fail"` → send back to the Explanation Agent to regenerate. **Max 2 retries**, then fall back to a plain template rendering of the numbers.

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

## 11. Final API response → Frontend

**Owner: Hemant** · The backend adds the name back here — *after* the agents have run.

```json
{
  "customer_name": "Rahul",
  "profile": { "...": "§2 output" },
  "risk": { "...": "§3 output" },
  "plans": [
    { "...": "§7 plan object merged with §8 plans_text entry" }
  ],
  "challenge": { "...": "§10 output, only after the customer picks" },
  "verifier": { "status": "pass" }
}
```

---

## 12. API endpoints

**Owner: Hemant**

| Method | Path | Body | Returns |
|---|---|---|---|
| `POST` | `/api/plan` | customer form or `{"customer_id": "C001"}` | §11 |
| `POST` | `/api/challenge` | `{"customer_id": "C001", "chosen_plan_id": "C"}` | §10 |
| `POST` | `/api/whatif` | `{"customer_id": "C001", "extra_monthly_savings": 10000}` | §11 recomputed |

Frontend form body for `/api/plan`:

```json
{
  "age": 28,
  "monthly_income": 120000,
  "assets": 800000,
  "liabilities": 200000,
  "stated_risk": "aggressive",
  "goals": [
    { "name": "house_downpayment", "target_amount": 2500000, "years": 5, "priority": 1 }
  ]
}
```

---

## 13. Mock files — commit these today

So nobody is ever blocked:

```
/mocks
  customer_C001.json      → §1   (Tiya)
  profile_out.json        → §2   (Tiya)
  features_out.json       → §3a  (Varada)
  risk_out.json           → §3   (core pod)
  plans_out.json          → §4   (Hemant)
  montecarlo_out.json     → §5   (Hemant)
  stress_out.json         → §6   (Pushkar)
  plan_bundle.json        → §7   (Shlok)
  explanation_out.json    → §8   (Madhura)
  api_response.json       → §11  (Hemant)
```

**Everyone commits their mock file today, filled with realistic fake values.** Supriya builds the entire UI against `api_response.json`. Madhura writes prompts against `plan_bundle.json`. Nobody waits.

---

## 14. Ownership summary

There is **no team leader**. Ownership is per-module and every module below has exactly one name that answers for it.

**Core pod — Shlok, Pushkar, Saurabh.** These three work as one unit on the ML model and the agent spine (§3b, §6, §7, §9). Everything else has a single owner.

| § | Module | Owner |
|---|---|---|
| 1 | Synthetic Data Generator | Tiya (schema with Varada) |
| 2 | Profile Engine | Tiya |
| 3a | Feature extraction (`features.py`) | Varada |
| 3b | Revealed Risk model training ⭐ | Core pod |
| 4 | Plan Generator + `assumptions.json` | Hemant |
| 5 | Monte Carlo + historical returns CSV | Hemant |
| 6 | Stress Test + `shocks.json` ⭐ | Pushkar (with Saurabh) |
| 7 | Orchestrator + `plan_bundle` | Shlok |
| 8 | Explanation Agent | Madhura |
| 9 | Verifier Agent ⭐ | Pushkar (with Shlok) |
| 10 | Challenger Agent | Madhura |
| 11–12 | API layer + finance-assumption correctness | Hemant |
| — | Frontend / UI | Supriya (+ Tiya from 27 Aug) |
| — | Pitch narrative + demo script | Madhura |
| — | Deck visuals + screen design | Supriya |
| — | Integration testing / QA | Pushkar |

### Rules instead of a leader

- **Feature freeze: 29 Aug.** Agreed by everyone in writing on Day 1, so it is the group's rule and not a person's order.
- **Contract changes go to the group first**, never silently.
- **Stuck for 3+ hours → say it in the group.** No exceptions, and this applies loudest to the core pod.
- **Daily standup, fixed time, 10 minutes**, three questions each: what finished, what's next, what's blocking.

---

## 15. Three things that must be true by tonight

1. This contract is agreed by everyone — read it and confirm in the group.
2. All mock files in `/mocks` are committed with realistic values.
3. Tiya's rough synthetic data generator produces at least one valid `C001` record.

Nothing else matters today.
