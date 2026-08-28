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


def _generate_investment_events(rng, ground_truth_risk):
    """Generate 2–6 investment events over the last ~3 years.  The number
    of panic sells correlates with ground_truth_risk but is noisy, so the
    label cannot be recovered from a single clean rule."""
    events = []
    n_events = rng.randint(2, 6)

    # More conservative ground truth → more likely to have panic sells
    panic_prob = {"conservative": 0.7, "moderate": 0.45, "aggressive": 0.15}
    p = panic_prob[ground_truth_risk]

    base_year = 2024
    for i in range(n_events):
        year = base_year + rng.choice([0, 0, 1])
        month = rng.randint(1, 12)
        day = rng.randint(1, 28)
        date = f"{year}-{month:02d}-{day:02d}"

        action = rng.choice(["buy", "sell"])
        amount = rng.randint(5, 40) * 10000
        instrument = "equity_mf"

        if action == "sell" and rng.random() < p:
            # panic sell during a market drop
            market_drawdown_pct = round(rng.uniform(3.0, 15.0), 1)
            days_after_drop = rng.randint(1, 10)
        elif action == "sell":
            # calm-market sell — not a panic sell
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

    # Sort by date
    events.sort(key=lambda e: e["date"])
    return events


def _assign_ground_truth_risk(rng, age, dependents, employment_type,
                               monthly_income, savings, equity_mf,
                               total_assets):
    """Assign ground_truth_risk using multiple noisy signals, not a single
    clean rule.  The contract explicitly requires confounders so the ML
    model cannot just relearn the generation rule."""
    score = 0.0

    # Age signal (younger → more aggressive, but noisy)
    if age < 30:
        score += rng.uniform(0.5, 1.5)
    elif age < 45:
        score += rng.uniform(-0.3, 0.8)
    else:
        score += rng.uniform(-1.0, 0.3)

    # Dependents signal (fewer → more aggressive)
    if dependents == 0:
        score += rng.uniform(0.3, 1.0)
    elif dependents <= 2:
        score += rng.uniform(-0.3, 0.4)
    else:
        score += rng.uniform(-0.8, -0.1)

    # Employment stability (salaried → slightly more aggressive capacity)
    if employment_type == "salaried":
        score += rng.uniform(0.0, 0.5)

    # Savings buffer (higher relative savings → more conservative behaviour
    # — this is a deliberate confounder: well-buffered people often ARE more
    # conservative in practice, which contradicts the capacity signal)
    savings_ratio = savings / max(monthly_income, 1)
    if savings_ratio > 3.0:
        score += rng.uniform(-0.6, 0.0)
    elif savings_ratio > 1.0:
        score += rng.uniform(-0.2, 0.3)

    # Equity tilt (higher equity allocation → aggressive behaviour)
    if total_assets > 0:
        eq_pct = equity_mf / total_assets
        score += rng.uniform(-0.2, 0.5) * eq_pct * 2

    # Pure noise confounder — makes the label unpredictable from any subset
    score += rng.uniform(-0.4, 0.4)

    if score > 1.5:
        return "aggressive"
    elif score > 0.3:
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

    # Ground truth risk — noisy, multi-signal, with confounders
    ground_truth_risk = _assign_ground_truth_risk(
        rng, age, dependents, employment_type,
        monthly_income, savings_account, equity_mf, total_assets,
    )

    # Transactions — at least 24 distinct calendar months
    transactions = _generate_transactions(rng, monthly_income, n_months=24)

    # Investment events — correlated with ground_truth_risk but noisy
    investment_events = _generate_investment_events(rng, ground_truth_risk)

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

