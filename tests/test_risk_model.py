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


# ── predict() tests ─────────────────────────────────────────────────────────

from models.risk_model import predict

def test_predict_validity_and_echo():
    """predict() must return a valid contract dict and echo features exactly."""
    features = {
        "panic_sell_count": 2,
        "avg_days_to_exit_after_drop": 3.0,
        "expense_volatility": 0.34,
        "emergency_fund_months": 0.4,
        "equity_allocation_pct": 0.5,
        "budget_overshoot_rate": 0.42
    }
    res = predict(features, stated_risk="aggressive")
    
    assert res["stated_risk"] == "aggressive"
    assert res["revealed_risk"] in RISK_LEVELS
    assert 0.0 <= res["confidence"] <= 1.0
    assert res["mismatch"] == (res["revealed_risk"] != "aggressive")
    assert res["features_used"] == features
    assert res["evidence"] == []
    assert res["model_version"] == "rr-v1"


def test_predict_deterministic():
    """Repeated predictions on the same features must be identical."""
    features = {
        "panic_sell_count": 1,
        "avg_days_to_exit_after_drop": 5.0,
        "expense_volatility": 0.1,
        "emergency_fund_months": 2.0,
        "equity_allocation_pct": 0.3,
        "budget_overshoot_rate": 0.3
    }
    r1 = predict(features, "moderate")
    r2 = predict(features, "moderate")
    assert r1 == r2


def test_predict_mismatch_calculation():
    """mismatch must be strictly evaluated as stated_risk != revealed_risk."""
    features = {
        "panic_sell_count": 0,
        "avg_days_to_exit_after_drop": None,
        "expense_volatility": 0.1,
        "emergency_fund_months": 2.0,
        "equity_allocation_pct": 0.3,
        "budget_overshoot_rate": 0.3
    }
    # We don't know the exact predicted class without checking, so we'll test both sides
    res1 = predict(features, "aggressive")
    res2 = predict(features, res1["revealed_risk"])
    
    assert res1["mismatch"] == (res1["revealed_risk"] != "aggressive")
    assert res2["mismatch"] is False


def test_predict_nullable_avg_days():
    """Missing avg_days_to_exit_after_drop must not throw an error (it is imputed)."""
    features = {
        "panic_sell_count": 0,
        "avg_days_to_exit_after_drop": None,
        "expense_volatility": 0.1,
        "emergency_fund_months": 3.0,
        "equity_allocation_pct": 0.2,
        "budget_overshoot_rate": 0.2
    }
    res = predict(features, "moderate")
    assert res["revealed_risk"] in RISK_LEVELS


def test_all_classes_can_be_predicted():
    """Across a broad range of features, all three labels must be reachable."""
    predictions = set()
    
    # Fake extremes to coax the model into predicting each class
    # 1. Very conservative
    predictions.add(predict({
        "panic_sell_count": 5,
        "avg_days_to_exit_after_drop": 1.0,
        "expense_volatility": 0.2,
        "emergency_fund_months": 12.0,
        "equity_allocation_pct": 0.05,
        "budget_overshoot_rate": 0.8
    }, "moderate")["revealed_risk"])
    
    # 2. Very aggressive
    predictions.add(predict({
        "panic_sell_count": 0,
        "avg_days_to_exit_after_drop": None,
        "expense_volatility": 0.05,
        "emergency_fund_months": 0.1,
        "equity_allocation_pct": 0.9,
        "budget_overshoot_rate": 0.1
    }, "moderate")["revealed_risk"])
    
    # 3. Moderate
    predictions.add(predict({
        "panic_sell_count": 1,
        "avg_days_to_exit_after_drop": 7.0,
        "expense_volatility": 0.12,
        "emergency_fund_months": 2.3,
        "equity_allocation_pct": 0.5,
        "budget_overshoot_rate": 0.58
    }, "moderate")["revealed_risk"])
    
    assert predictions == RISK_LEVELS
