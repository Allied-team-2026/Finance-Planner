"""Tests for features.py Revealed Risk Feature Extraction Engine."""

import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from features import (
    CORE_FEATURE_NAMES,
    clean_customer_data,
    clean_single_customer_data,
    extract_features_single,
    extract_features_batch,
    extract_feature_matrix,
)


@pytest.fixture
def sample_customer_c001():
    """Load mock C001 customer record."""
    mock_path = Path(__file__).resolve().parent.parent / "mocks" / "customer_C001.json"
    if mock_path.exists():
        with open(mock_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "customer_id": "C001",
        "age": 28,
        "stated_risk": "aggressive",
        "monthly_income": 120000,
        "assets": {"savings_account": 300000, "equity_mf": 400000, "fixed_deposit": 100000},
        "liabilities": [{"type": "car_loan", "outstanding": 200000, "emi": 8000}],
        "transactions": [
            {"date": "2025-01-05", "category": "rent", "amount": 25000},
            {"date": "2025-02-05", "category": "rent", "amount": 28000},
        ],
        "investment_events": [
            {"date": "2024-03-12", "action": "sell", "amount": 150000, "market_drawdown_pct": 9.0, "days_after_drop": 3.0}
        ],
    }


def test_core_feature_names_present(sample_customer_c001):
    """Confirm single feature extraction output has the exact contract keys."""
    features = extract_features_single(sample_customer_c001)
    
    assert set(features.keys()) == set(CORE_FEATURE_NAMES)
    assert len(features) == 6


def test_correct_data_types(sample_customer_c001):
    """Verify that single and batch outputs have strictly correct numeric data types."""
    features = extract_features_single(sample_customer_c001)
    
    assert isinstance(features["panic_sell_count"], int)
    assert isinstance(features["avg_days_to_exit_after_drop"], float)
    assert isinstance(features["expense_volatility"], float)
    assert isinstance(features["emergency_fund_months"], float)
    assert isinstance(features["equity_allocation_pct"], float)
    assert isinstance(features["budget_overshoot_rate"], float)

    # Test batch DataFrame types
    df = extract_features_batch([sample_customer_c001])
    assert df["panic_sell_count"].dtype == np.int64
    assert df["avg_days_to_exit_after_drop"].dtype == np.float64
    assert df["expense_volatility"].dtype == np.float64
    assert df["emergency_fund_months"].dtype == np.float64
    assert df["equity_allocation_pct"].dtype == np.float64
    assert df["budget_overshoot_rate"].dtype == np.float64


def test_no_nans_or_infs_in_output():
    """Verify that feature extraction never emits NaN or Infinite values under any edge case."""
    edge_cases = [
        # Empty customer
        {"customer_id": "EMPTY"},
        # Customer with all zero assets and liabilities
        {
            "customer_id": "ZEROES",
            "assets": {"savings_account": 0, "equity_mf": 0},
            "liabilities": [],
            "transactions": [],
            "investment_events": [],
        },
        # Customer with nulls in fields
        {
            "customer_id": "NULLS",
            "monthly_income": None,
            "assets": {"savings_account": None, "equity_mf": None},
            "transactions": [
                {"date": "2025-01-01", "category": "rent", "amount": None},
                {"date": None, "category": None, "amount": 1000},
            ],
            "investment_events": [
                {"date": "2025-01-01", "action": "sell", "market_drawdown_pct": None, "days_after_drop": None}
            ],
        },
    ]

    for record in edge_cases:
        feat = extract_features_single(record)
        for key, val in feat.items():
            assert val is not None, f"Feature {key} is None for {record['customer_id']}"
            assert not np.isnan(val), f"Feature {key} is NaN for {record['customer_id']}"
            assert not np.isinf(val), f"Feature {key} is Infinite for {record['customer_id']}"

    df_batch = extract_features_batch(edge_cases)
    assert df_batch.isna().sum().sum() == 0
    assert not np.isinf(df_batch.to_numpy()).any()


def test_transaction_deduplication():
    """Test that identical duplicate transactions are removed during cleaning."""
    record = {
        "customer_id": "DEDUP_TEST",
        "transactions": [
            {"date": "2025-01-05", "category": "rent", "amount": 25000},
            {"date": "2025-01-05", "category": "rent", "amount": 25000},  # Duplicate
            {"date": "2025-01-05", "category": "rent", "amount": 25000},  # Duplicate
            {"date": "2025-01-06", "category": "groceries", "amount": 3000},
        ],
    }
    cleaned = clean_single_customer_data(record)
    assert len(cleaned["transactions"]) == 2


def test_panic_sell_calculation_logic():
    """Test precise calculation of panic sells and exit timing."""
    record = {
        "customer_id": "PANIC_TEST",
        "assets": {"savings_account": 100000, "equity_mf": 300000},
        "investment_events": [
            {"date": "2024-03-12", "action": "sell", "amount": 100000, "market_drawdown_pct": 8.0, "days_after_drop": 2.0},
            {"date": "2024-06-15", "action": "sell", "amount": 50000, "market_drawdown_pct": 12.0, "days_after_drop": 6.0},
            {"date": "2024-09-20", "action": "buy", "amount": 20000, "market_drawdown_pct": 5.0, "days_after_drop": 1.0},  # Buy, not sell
            {"date": "2024-11-10", "action": "sell", "amount": 30000, "market_drawdown_pct": 0.0, "days_after_drop": 0.0},  # Not a drawdown
        ],
    }

    features = extract_features_single(record)
    assert features["panic_sell_count"] == 2
    assert features["avg_days_to_exit_after_drop"] == 4.0  # (2 + 6) / 2
    assert features["equity_allocation_pct"] == 0.75  # 300000 / 400000


def test_features_matrix_numpy_shape(sample_customer_c001):
    """Test numpy feature matrix extraction for ML readiness."""
    records = [sample_customer_c001, sample_customer_c001]
    matrix = extract_feature_matrix(records)
    
    assert isinstance(matrix, np.ndarray)
    assert matrix.shape == (2, 6)
    assert matrix.dtype == np.float64
    assert np.isnan(matrix).sum() == 0


def test_mock_features_out_json_validity():
    """Ensure the committed mocks/features_out.json matches all contract requirements."""
    mock_file = Path(__file__).resolve().parent.parent / "mocks" / "features_out.json"
    assert mock_file.exists()
    
    with open(mock_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    for field in CORE_FEATURE_NAMES:
        assert field in data, f"Missing field in features_out.json: {field}"
        assert data[field] is not None
        assert not np.isnan(data[field])
