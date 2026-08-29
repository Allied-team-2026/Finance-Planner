"""§1 Synthetic Data Generator — produces one valid customer record per call.

Deterministic for a given (seed, customer_id) pair.  Does NOT contain the
three fixed demo personas (C001/C002/C003) — those are hand-written mocks.
"""

import random
import json
from pathlib import Path

# ── constants from the frozen contract ──────────────────────────────────────

RISK_LEVELS = ["conservative", "moderate", "aggressive"]
EMPLOYMENT_TYPES = ["salaried", "self_employed", "business_owner"]
CITY_TIERS = ["metro", "tier_2", "tier_3"]
TRANSACTION_CATEGORIES = [
    "rent", "groceries", "utilities", "transport", "dining",
    "shopping", "health", "education", "entertainment", "emi",
    "insurance", "misc",
]
GOAL_NAMES = [
    "house_downpayment", "child_education", "retirement",
    "car_purchase", "emergency_fund", "vacation", "wedding",
]
LIABILITY_TYPES = ["car_loan", "home_loan", "personal_loan", "education_loan"]
FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh",
    "Ayaan", "Krishna", "Ishaan", "Ananya", "Diya", "Myra", "Sara",
    "Aanya", "Aadhya", "Ira", "Kiara", "Priya", "Neha",
]
LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Mehta", "Patel", "Reddy", "Nair",
    "Iyer", "Singh", "Kumar", "Joshi", "Das", "Bhat", "Rao", "Menon",
]


def _month_range(rng, n_months=24):
    """Return a list of (year, month) tuples going back n_months from a
    synthetic 'now' of 2026-07."""
    base_year, base_month = 2026, 7
    months = []
    for i in range(n_months):
        m = base_month - i
        y = base_year
        while m <= 0:
            m += 12
            y -= 1
        months.append((y, m))
    months.reverse()
    return months


def _generate_transactions(rng, monthly_income, n_months=24):
    """Generate realistic transactions spanning n_months distinct calendar
    months.  Each month gets 8–15 transactions across random categories,
    with a total that is a noisy fraction of monthly_income."""
    months = _month_range(rng, n_months)
    transactions = []

    # Base spending proportions — rent is always the largest
    base_proportions = {
        "rent": 0.30, "groceries": 0.14, "utilities": 0.05,
        "transport": 0.07, "dining": 0.06, "shopping": 0.04,
        "health": 0.03, "education": 0.02, "entertainment": 0.03,
        "emi": 0.08, "insurance": 0.03, "misc": 0.15,
    }

    for year, month in months:
        # Each month's total spend is 50%–75% of income, with noise
        spend_ratio = rng.uniform(0.50, 0.75)
        month_budget = int(monthly_income * spend_ratio)

        n_txns = rng.randint(8, 15)
        # Pick categories for this month (always include rent and groceries)
        cats = ["rent", "groceries"]
        remaining = [c for c in TRANSACTION_CATEGORIES if c not in cats]
        extra = rng.sample(remaining, min(n_txns - 2, len(remaining)))
        cats.extend(extra)
        rng.shuffle(cats)

        # Distribute budget across categories with noise
        raw_weights = []
        for cat in cats:
            base = base_proportions.get(cat, 0.05)
            raw_weights.append(base * rng.uniform(0.5, 1.5))
        total_weight = sum(raw_weights)

        for i, cat in enumerate(cats):
            share = raw_weights[i] / total_weight
            amount = max(500, int(round(month_budget * share, -2)))
            day = rng.randint(1, 28)
            transactions.append({
                "date": f"{year}-{month:02d}-{day:02d}",
                "category": cat,
                "amount": amount,
            })

    return transactions


def _generate_investment_events(rng):
    """Generate 2–6 investment events over the last ~3 years.

    Panic-sell probability is fixed (not label-dependent) so the resulting
    panic_sell_count and avg_days_to_exit are purely stochastic and can
    serve as honest inputs to the label-assignment step.
    """
    events = []
    n_events = rng.randint(2, 6)
    panic_prob = 0.40  # fixed probability — creates natural variation

    base_year = 2024
    for i in range(n_events):
        year = base_year + rng.choice([0, 0, 1])
        month = rng.randint(1, 12)
        day = rng.randint(1, 28)
        date = f"{year}-{month:02d}-{day:02d}"

        action = rng.choice(["buy", "sell"])
        amount = rng.randint(5, 40) * 10000
        instrument = "equity_mf"

        if action == "sell" and rng.random() < panic_prob:
            market_drawdown_pct = round(rng.uniform(3.0, 15.0), 1)
            days_after_drop = rng.randint(1, 10)
        elif action == "sell":
            market_drawdown_pct = 0.0
            days_after_drop = None
        else:
            market_drawdown_pct = 0.0
            days_after_drop = None

        events.append({
            "date": date,
            "action": action,
            "instrument": instrument,
            "amount": amount,
            "market_drawdown_pct": market_drawdown_pct,
            "days_after_drop": days_after_drop,
        })

    events.sort(key=lambda e: e["date"])
    return events


def _compute_feature_proxies(transactions, investment_events,
                              savings, equity_mf, total_assets):
    """Compute approximate values of the six §3a observable features inline.

    These are the same quantities that engines/features.py and
    engines/profile.py would produce, but computed here without importing
    those modules (to avoid circular dependencies).
    """
    # ── panic sells ─────────────────────────────────────────────────────
    panic_sells = [
        e for e in investment_events
        if e["action"] == "sell" and e.get("days_after_drop") is not None
    ]
    panic_sell_count = len(panic_sells)

    if panic_sell_count > 0:
        avg_days_to_exit = (
            sum(e["days_after_drop"] for e in panic_sells) / panic_sell_count
        )
    else:
        avg_days_to_exit = 5.5  # neutral midpoint for scoring

    # ── monthly expense statistics (last 12 months) ────────────────────
    month_totals = {}
    for t in transactions:
        m = t["date"][:7]
        month_totals[m] = month_totals.get(m, 0) + t["amount"]
    sorted_months = sorted(month_totals.keys())[-12:]
    monthly_vals = [month_totals[m] for m in sorted_months]

    mean_expense = sum(monthly_vals) / len(monthly_vals) if monthly_vals else 1

    if len(monthly_vals) >= 2:
        var = sum((x - mean_expense) ** 2 for x in monthly_vals) / (len(monthly_vals) - 1)
        expense_volatility = (var ** 0.5) / mean_expense
    else:
        expense_volatility = 0.0

    emergency_fund_months = savings / mean_expense if mean_expense > 0 else 0.0

    equity_allocation_pct = equity_mf / total_assets if total_assets > 0 else 0.0

    overshoot = sum(1 for x in monthly_vals if x > mean_expense)
    budget_overshoot_rate = overshoot / len(monthly_vals) if monthly_vals else 0.0

    return {
        "panic_sell_count": panic_sell_count,
        "avg_days_to_exit": avg_days_to_exit,
        "expense_volatility": expense_volatility,
        "emergency_fund_months": emergency_fund_months,
        "equity_allocation_pct": equity_allocation_pct,
        "budget_overshoot_rate": budget_overshoot_rate,
    }


def _assign_ground_truth_risk(rng, proxies):
    """Assign ground_truth_risk from the six observable features + noise.

    Every feature contributes a centered score (mean ≈ 0 for a typical
    customer).  Two independent noise terms (Gaussian + uniform confounder)
    ensure no single feature deterministically defines the label.

    Higher score → more aggressive.  Lower score → more conservative.
    """
    score = 0.0

    # ── feature signals (centered around typical values) ────────────────
    # panic_sell_count: more panics → conservative
    score -= (proxies["panic_sell_count"] - 0.8) * 0.25

    # avg_days_to_exit: faster exit → conservative, slower → aggressive
    score += (proxies["avg_days_to_exit"] - 5.5) * 0.10

    # expense_volatility: higher volatility → conservative
    score -= (proxies["expense_volatility"] - 0.11) * 1.0

    # emergency_fund_months: larger buffer → conservative
    score -= (proxies["emergency_fund_months"] - 3.5) * 0.10

    # equity_allocation_pct: more equity → aggressive
    score += (proxies["equity_allocation_pct"] - 0.40) * 1.0

    # budget_overshoot_rate: more overshoots → weakly conservative
    score -= (proxies["budget_overshoot_rate"] - 0.50) * 0.50

    # ── noise + confounder ──────────────────────────────────────────────
    score += rng.gauss(0, 0.20)       # Gaussian noise
    score += rng.uniform(-0.12, 0.12) # independent uniform confounder

    if score > 0.20:
        return "aggressive"
    elif score > -0.20:
        return "moderate"
    else:
        return "conservative"


def generate_customer(seed, customer_id):
    """Generate one synthetic customer record, deterministic for the given
    seed and customer_id.  Returns a dict matching the §1 contract schema."""
    rng = random.Random(seed)

    name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
    age = rng.randint(22, 60)
    dependents = rng.choices([0, 1, 2, 3, 4], weights=[30, 30, 20, 15, 5])[0]
    employment_type = rng.choice(EMPLOYMENT_TYPES)
    city_tier = rng.choice(CITY_TIERS)
    stated_risk = rng.choice(RISK_LEVELS)
    monthly_income = rng.randint(30, 300) * 1000

    # Assets
    savings_account = rng.randint(1, 50) * 10000
    equity_mf = rng.randint(0, 80) * 10000
    fixed_deposit = rng.randint(0, 60) * 10000
    assets = {
        "savings_account": savings_account,
        "equity_mf": equity_mf,
        "fixed_deposit": fixed_deposit,
    }
    total_assets = savings_account + equity_mf + fixed_deposit

    # Liabilities (0–2 loans)
    n_loans = rng.choices([0, 1, 2], weights=[30, 50, 20])[0]
    liabilities = []
    for _ in range(n_loans):
        loan_type = rng.choice(LIABILITY_TYPES)
        outstanding = rng.randint(5, 100) * 10000
        emi = max(1000, int(round(outstanding * rng.uniform(0.02, 0.06), -3)))
        liabilities.append({
            "type": loan_type,
            "outstanding": outstanding,
            "emi": emi,
        })

    # Goals (1–3)
    n_goals = rng.randint(1, 3)
    used_goal_names = rng.sample(GOAL_NAMES, n_goals)
    goals = []
    for i, gname in enumerate(used_goal_names):
        goals.append({
            "name": gname,
            "target_amount": rng.randint(5, 100) * 50000,
            "years": rng.randint(2, 15),
            "priority": i + 1,
        })

    # Transactions — at least 24 distinct calendar months
    transactions = _generate_transactions(rng, monthly_income, n_months=24)

    # Investment events — stochastic, not label-dependent
    investment_events = _generate_investment_events(rng)

    # Compute feature proxies from the generated data
    proxies = _compute_feature_proxies(
        transactions, investment_events,
        savings_account, equity_mf, total_assets,
    )

    # Ground truth risk — derived from observable features + controlled noise
    ground_truth_risk = _assign_ground_truth_risk(rng, proxies)

    return {
        "customer_id": customer_id,
        "name": name,
        "age": age,
        "dependents": dependents,
        "employment_type": employment_type,
        "city_tier": city_tier,
        "stated_risk": stated_risk,
        "monthly_income": monthly_income,
        "assets": assets,
        "liabilities": liabilities,
        "goals": goals,
        "transactions": transactions,
        "investment_events": investment_events,
        "ground_truth_risk": ground_truth_risk,
    }

def generate_dataset(count=1000, seed=42):
    """Generate a deterministic dataset of `count` synthetic customers.

    Each customer gets a unique ID (G0001, G0002, ...) and a per-customer
    seed derived from the master seed, so the full dataset is reproducible
    from `generate_dataset(count, seed)` alone.
    """
    master_rng = random.Random(seed)
    dataset = []
    for i in range(count):
        customer_seed = master_rng.randint(0, 2**31 - 1)
        customer_id = f"G{i + 1:04d}"
        dataset.append(generate_customer(customer_seed, customer_id))
    return dataset


def load_customer(customer_id="C001"):
    """Load a hand-written demo customer from the mocks directory.
    Used by the orchestrator pipeline when a real engine is not yet wired."""
    mocks = Path(__file__).resolve().parent.parent / "mocks"
    path = mocks / f"customer_{customer_id}.json"
    return json.loads(path.read_text())

