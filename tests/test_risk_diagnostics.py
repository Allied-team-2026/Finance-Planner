"""Tests for the §3b feature diagnostics."""

from models.risk_diagnostics import (
    FEATURE_ORDER,
    LABEL_ORDER,
    load_records,
    compute_diagnostics,
)


def test_all_features_included():
    """The diagnostic must cover all six contract features."""
    records = load_records()
    diag = compute_diagnostics(records)
    assert set(diag["features"].keys()) == set(FEATURE_ORDER)


def test_all_labels_present():
    """Each feature's by_class must contain all three risk labels."""
    records = load_records()
    diag = compute_diagnostics(records)
    for feat in FEATURE_ORDER:
        assert set(diag["features"][feat]["by_class"].keys()) == set(LABEL_ORDER)


def test_no_unexpected_missing_values():
    """Only avg_days_to_exit_after_drop may have missing values (null for
    zero-panic-sell customers); all others must have zero missing."""
    records = load_records()
    diag = compute_diagnostics(records)
    for feat in FEATURE_ORDER:
        missing = diag["features"][feat]["overall"]["missing"]
        if feat == "avg_days_to_exit_after_drop":
            # Some missing is expected and valid
            assert missing >= 0
        else:
            assert missing == 0, f"{feat} has {missing} unexpected missing values"


def test_deterministic_output():
    """Running compute_diagnostics twice must produce identical results."""
    records = load_records()
    d1 = compute_diagnostics(records)
    d2 = compute_diagnostics(records)
    assert d1 == d2


def test_separability_is_sorted():
    """The separability list must be sorted descending by abs_std_mean_diff."""
    records = load_records()
    diag = compute_diagnostics(records)
    diffs = [e["abs_std_mean_diff"] for e in diag["separability"]]
    assert diffs == sorted(diffs, reverse=True)
