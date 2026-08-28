"""Tests for the §3a training feature dataset in data/training_features.json."""

import json
from collections import Counter
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent / "data" / "training_features.json"

RISK_LEVELS = {"conservative", "moderate", "aggressive"}
FEATURE_KEYS = {
    "panic_sell_count",
    "avg_days_to_exit_after_drop",
    "expense_volatility",
    "emergency_fund_months",
    "equity_allocation_pct",
    "budget_overshoot_rate",
}

# Disallowed keys — raw customer data must not leak into the feature file
RAW_CUSTOMER_KEYS = {
    "name", "age", "dependents", "employment_type", "city_tier",
    "stated_risk", "monthly_income", "assets", "liabilities",
    "goals", "transactions", "investment_events",
}


def _load():
    return json.loads(DATA_PATH.read_text())


def test_file_exists():
    """The training feature file must exist."""
    assert DATA_PATH.exists(), f"{DATA_PATH} not found"


def test_exactly_1000_records():
    """The dataset must contain exactly 1,000 records."""
    data = _load()
    assert len(data) == 1000


def test_record_structure():
    """Each record has exactly customer_id, features, and ground_truth_risk."""
    data = _load()
    for r in data:
        assert set(r.keys()) == {"customer_id", "features", "ground_truth_risk"}
        assert set(r["features"].keys()) == FEATURE_KEYS


def test_no_raw_customer_fields():
    """No raw customer data may appear in any record."""
    data = _load()
    for r in data:
        assert not RAW_CUSTOMER_KEYS & set(r.keys()), \
            f"Raw customer keys leaked into record {r['customer_id']}"


def test_valid_risk_labels():
    """Every ground_truth_risk must be one of the three allowed values."""
    data = _load()
    for r in data:
        assert r["ground_truth_risk"] in RISK_LEVELS


def test_all_labels_present():
    """All three risk labels must occur in the dataset."""
    data = _load()
    labels = set(r["ground_truth_risk"] for r in data)
    assert labels == RISK_LEVELS


def test_no_missing_features():
    """Every feature value must be non-null and numeric, except
    avg_days_to_exit_after_drop which is null when panic_sell_count is 0."""
    data = _load()
    for r in data:
        for k, v in r["features"].items():
            if k == "avg_days_to_exit_after_drop" and r["features"]["panic_sell_count"] == 0:
                assert v is None, f"{r['customer_id']}.{k} should be None when no panic sells"
                continue
            assert v is not None, f"{r['customer_id']}.{k} is None"
            assert isinstance(v, (int, float)), f"{r['customer_id']}.{k} is {type(v)}"


def test_feature_values_vary():
    """Features must show variation across the dataset — not all identical."""
    data = _load()
    for key in FEATURE_KEYS:
        values = set(r["features"][key] for r in data)
        assert len(values) > 1, f"{key} has a single value across all 1000 records"


def test_deterministic_regeneration():
    """Regenerating with the same seed must produce identical content."""
    from engines.synthetic_data import generate_dataset
    from engines.profile import build_profile
    from engines.features import extract

    feature_order = [
        "panic_sell_count", "avg_days_to_exit_after_drop",
        "expense_volatility", "emergency_fund_months",
        "equity_allocation_pct", "budget_overshoot_rate",
    ]

    saved = _load()
    customers = generate_dataset(1000, 42)
    for i, c in enumerate(customers):
        profile = build_profile(c)
        features = extract(c, profile)
        expected = {k: features[k] for k in feature_order}
        assert saved[i]["customer_id"] == c["customer_id"]
        assert saved[i]["features"] == expected
        assert saved[i]["ground_truth_risk"] == c["ground_truth_risk"]
