"""Tests for the §1 Synthetic Data Generator."""

from collections import Counter
from engines.synthetic_data import generate_customer, generate_dataset

RISK_LEVELS = {"conservative", "moderate", "aggressive"}
EMPLOYMENT_TYPES = {"salaried", "self_employed", "business_owner"}
CITY_TIERS = {"metro", "tier_2", "tier_3"}
TRANSACTION_CATEGORIES = {
    "rent", "groceries", "utilities", "transport", "dining",
    "shopping", "health", "education", "entertainment", "emi",
    "insurance", "misc",
}


def test_schema_validity():
    """Every required §1 field is present and has the correct type."""
    c = generate_customer(42, "T001")

    assert isinstance(c["customer_id"], str) and c["customer_id"] == "T001"
    assert isinstance(c["name"], str) and len(c["name"]) > 0
    assert isinstance(c["age"], int) and 18 <= c["age"] <= 80
    assert isinstance(c["dependents"], int) and c["dependents"] >= 0
    assert c["employment_type"] in EMPLOYMENT_TYPES
    assert c["city_tier"] in CITY_TIERS
    assert c["stated_risk"] in RISK_LEVELS
    assert isinstance(c["monthly_income"], int) and c["monthly_income"] > 0

    # Assets
    assert isinstance(c["assets"], dict)
    for k in ("savings_account", "equity_mf", "fixed_deposit"):
        assert k in c["assets"]
        assert isinstance(c["assets"][k], int)

    # Liabilities
    assert isinstance(c["liabilities"], list)
    for loan in c["liabilities"]:
        assert "type" in loan and "outstanding" in loan and "emi" in loan
        assert isinstance(loan["outstanding"], int)
        assert isinstance(loan["emi"], int)

    # Goals — at least one
    assert isinstance(c["goals"], list) and len(c["goals"]) >= 1
    for g in c["goals"]:
        assert "name" in g and "target_amount" in g and "years" in g and "priority" in g

    # Transactions
    assert isinstance(c["transactions"], list) and len(c["transactions"]) > 0
    for t in c["transactions"]:
        assert "date" in t and "category" in t and "amount" in t
        assert t["category"] in TRANSACTION_CATEGORIES
        assert isinstance(t["amount"], int) and t["amount"] > 0

    # Investment events
    assert isinstance(c["investment_events"], list)
    for e in c["investment_events"]:
        assert "date" in e and "action" in e and "instrument" in e
        assert "amount" in e and "market_drawdown_pct" in e
        assert "days_after_drop" in e
        assert e["action"] in ("buy", "sell")


def test_24_distinct_transaction_months():
    """The contract requires at least 24 months of transaction history."""
    c = generate_customer(42, "T001")
    months = set(t["date"][:7] for t in c["transactions"])
    assert len(months) >= 24


def test_ground_truth_risk_valid():
    """ground_truth_risk must be one of the three permitted values."""
    for seed in range(10):
        c = generate_customer(seed, f"S{seed:03d}")
        assert c["ground_truth_risk"] in RISK_LEVELS


def test_deterministic_output():
    """The same (seed, customer_id) must produce identical output."""
    a = generate_customer(42, "T001")
    b = generate_customer(42, "T001")
    assert a == b


def test_different_seeds_differ():
    """Different seeds must produce different customers."""
    a = generate_customer(1, "T001")
    b = generate_customer(2, "T001")
    # At minimum, the name or income or assets should differ
    assert a != b


def test_investment_event_structure():
    """Investment events must conform to the contract structure."""
    c = generate_customer(42, "T001")
    for e in c["investment_events"]:
        # Buys must have drawdown 0.0 and days_after_drop null
        if e["action"] == "buy":
            assert e["market_drawdown_pct"] == 0.0
            assert e["days_after_drop"] is None
        # Sells during a drop must have positive drawdown and integer days
        if e["action"] == "sell" and e["days_after_drop"] is not None:
            assert e["market_drawdown_pct"] > 0
            assert isinstance(e["days_after_drop"], int)


# ── Dataset-level tests ────────────────────────────────────────────────────

import pytest

@pytest.fixture(scope="module")
def dataset_1000():
    """Generate the full 1000-customer dataset once for all dataset tests."""
    return generate_dataset(1000, 42)


def test_dataset_count(dataset_1000):
    """generate_dataset must return exactly 1000 customers."""
    assert len(dataset_1000) == 1000


def test_dataset_unique_ids(dataset_1000):
    """Every customer_id must be unique."""
    ids = [c["customer_id"] for c in dataset_1000]
    assert len(ids) == len(set(ids))


def test_dataset_deterministic():
    """Repeating generate_dataset with the same seed produces identical output."""
    a = generate_dataset(10, 99)
    b = generate_dataset(10, 99)
    assert a == b


def test_dataset_enums(dataset_1000):
    """Every customer's enums must be from the allowed sets."""
    for c in dataset_1000:
        assert c["employment_type"] in EMPLOYMENT_TYPES
        assert c["city_tier"] in CITY_TIERS
        assert c["stated_risk"] in RISK_LEVELS
        assert c["ground_truth_risk"] in RISK_LEVELS


def test_dataset_24_months(dataset_1000):
    """Every customer must have at least 24 distinct transaction months."""
    for c in dataset_1000:
        months = set(t["date"][:7] for t in c["transactions"])
        assert len(months) >= 24, f"{c['customer_id']} has {len(months)} months"


def test_dataset_risk_distribution(dataset_1000):
    """All three risk labels must occur and no class exceeds 70%."""
    counts = Counter(c["ground_truth_risk"] for c in dataset_1000)
    assert set(counts.keys()) == RISK_LEVELS, f"Missing labels: {RISK_LEVELS - set(counts.keys())}"
    for label, n in counts.items():
        assert n / 1000 <= 0.70, f"{label} is {n/1000:.0%} of the dataset, exceeds 70%"


def test_no_single_feature_determines_label(dataset_1000):
    """Prove that no single feature deterministically defines the label."""
    # Find customers with the same exact panic_sell_count but different labels
    # to prove panic_sell_count alone doesn't determine the label.
    # Note: we use the raw events to count panic sells for the test.
    from collections import defaultdict
    
    panic_groups = defaultdict(set)
    for c in dataset_1000:
        panic_sells = sum(1 for e in c["investment_events"] if e["action"] == "sell" and e.get("days_after_drop") is not None)
        panic_groups[panic_sells].add(c["ground_truth_risk"])
        
    # At least one group of same panic_sell_count should map to multiple labels
    assert any(len(labels) > 1 for labels in panic_groups.values()), "panic_sell_count deterministically defines the label"


