import json
from pathlib import Path
import pytest
from engines.profile import build_profile

EXPENSE_CATEGORIES = [
    "rent", "groceries", "utilities", "transport", "dining",
    "shopping", "health", "education", "entertainment",
    "emi", "insurance", "misc"
]

def load_c001():
    path = Path(__file__).resolve().parent.parent / "mocks" / "customer_C001.json"
    return json.loads(path.read_text())

def test_c001_has_12_months():
    c001 = load_c001()
    months = set(t["date"][:7] for t in c001["transactions"])
    assert len(months) == 12, "C001 must have exactly 12 distinct transaction months"

def test_c001_categories_are_permitted():
    c001 = load_c001()
    allowed_categories = set(EXPENSE_CATEGORIES)
    for t in c001["transactions"]:
        assert t["category"] in allowed_categories, f"Invalid category {t['category']}"

def test_c001_profile_expense_mean():
    c001 = load_c001()
    profile = build_profile(c001)
    # The profile engine averages the last 12 months.
    assert profile["monthly_expense"] == 75000, "The 12-month mean must be exactly 75,000"

def test_c001_transaction_history_is_variable():
    c001 = load_c001()
    # Calculate monthly totals
    totals = {}
    for t in c001["transactions"]:
        m = t["date"][:7]
        totals[m] = totals.get(m, 0) + t["amount"]
    
    unique_totals = set(totals.values())
    assert len(unique_totals) > 1, "Monthly totals must be variable, not identical every month"

def test_c001_panic_sells_remain():
    c001 = load_c001()
    panic_sells = [e for e in c001["investment_events"] if e["action"] == "sell" and e.get("days_after_drop") is not None]
    assert len(panic_sells) == 2, "C001 must retain exactly 2 panic sells"
