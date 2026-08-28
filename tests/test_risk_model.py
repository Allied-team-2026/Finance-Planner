"""Tests for the §3b baseline risk model (using the correlated dataset)."""

import numpy as np
from models.risk_model import (
    FEATURE_ORDER,
    LABEL_ORDER,
    load_dataset,
    split_data,
    train_baseline,
)

RISK_LEVELS = {"conservative", "moderate", "aggressive"}


def test_dataset_loads_correctly():
    """load_dataset returns the correct shapes and no NaN after imputation."""
    X, y, ids = load_dataset()
    assert X.shape == (1000, 6)
    assert y.shape == (1000,)
    assert len(ids) == 1000
    # No NaN after imputation
    assert not np.isnan(X).any(), "NaN found in feature matrix after imputation"


def test_feature_columns_in_order():
    """The six feature columns must match FEATURE_ORDER."""
    assert FEATURE_ORDER == [
        "panic_sell_count",
        "avg_days_to_exit_after_drop",
        "expense_volatility",
        "emergency_fund_months",
        "equity_allocation_pct",
        "budget_overshoot_rate",
    ]


def test_split_is_deterministic():
    """The stratified split must produce identical results on repeated calls."""
    X, y, _ = load_dataset()
    X_tr1, X_te1, y_tr1, y_te1 = split_data(X, y)
    X_tr2, X_te2, y_tr2, y_te2 = split_data(X, y)
    np.testing.assert_array_equal(X_tr1, X_tr2)
    np.testing.assert_array_equal(X_te1, X_te2)
    np.testing.assert_array_equal(y_tr1, y_tr2)
    np.testing.assert_array_equal(y_te1, y_te2)


def test_split_is_stratified():
    """Both train and test sets must contain all three risk labels."""
    X, y, _ = load_dataset()
    _, _, y_train, y_test = split_data(X, y)
    assert set(y_train) == RISK_LEVELS
    assert set(y_test) == RISK_LEVELS


def test_baseline_produces_valid_labels():
    """The trained baseline must predict only the three permitted labels."""
    X, y, _ = load_dataset()
    X_train, X_test, y_train, y_test = split_data(X, y)
    clf = train_baseline(X_train, y_train)
    y_pred = clf.predict(X_test)
    assert set(y_pred).issubset(RISK_LEVELS)
    # Must predict at least two distinct classes on a 200-sample test set
    assert len(set(y_pred)) >= 2
