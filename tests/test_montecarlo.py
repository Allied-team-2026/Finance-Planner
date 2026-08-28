"""
Tests for the §5 Monte Carlo historical-return loader and resampling helper.

Does NOT test the full simulate() API, which does not exist yet.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engines.montecarlo import load_historical_returns, sample_returns, simulate_path, simulate_plan  # noqa: E402
import pytest  # noqa: E402


# ------------------------------------------------------------------ loader

def test_load_returns_exactly_21_observations():
    obs = load_historical_returns()
    assert len(obs) == 21


def test_load_returns_first_year():
    obs = load_historical_returns()
    assert obs[0]["year"] == 2005


def test_load_returns_last_year():
    obs = load_historical_returns()
    assert obs[-1]["year"] == 2025


def test_load_returns_all_years_present():
    obs = load_historical_returns()
    years = [o["year"] for o in obs]
    assert years == list(range(2005, 2026))


def test_load_returns_are_numeric_decimals():
    obs = load_historical_returns()
    for o in obs:
        assert isinstance(o["annual_return"], float)
        assert -1.0 < o["annual_return"] < 2.0


# --------------------------------------------------------------- sampler

def test_sample_returns_length():
    returns = [o["annual_return"] for o in load_historical_returns()]
    sampled = sample_returns(returns, 20, seed=42)
    assert len(sampled) == 20


def test_sample_returns_deterministic():
    """Same seed and inputs must produce identical samples."""
    returns = [o["annual_return"] for o in load_historical_returns()]
    a = sample_returns(returns, 50, seed=42)
    b = sample_returns(returns, 50, seed=42)
    assert a == b


def test_sample_returns_different_seed():
    """Different seeds should (overwhelmingly likely) produce different samples."""
    returns = [o["annual_return"] for o in load_historical_returns()]
    a = sample_returns(returns, 50, seed=42)
    b = sample_returns(returns, 50, seed=99)
    assert a != b


def test_sample_returns_values_belong_to_historical():
    """Every sampled value must be one of the original historical observations."""
    returns = [o["annual_return"] for o in load_historical_returns()]
    historical_set = set(returns)
    sampled = sample_returns(returns, 200, seed=7)
    for v in sampled:
        assert v in historical_set


def test_sample_returns_with_replacement():
    """With 200 samples from 21 observations, duplicates are certain."""
    returns = [o["annual_return"] for o in load_historical_returns()]
    sampled = sample_returns(returns, 200, seed=7)
    assert len(set(sampled)) < len(sampled)


def test_sample_returns_zero_samples():
    returns = [o["annual_return"] for o in load_historical_returns()]
    sampled = sample_returns(returns, 0, seed=42)
    assert sampled == []


def test_sample_returns_empty_raises():
    with pytest.raises(ValueError):
        sample_returns([], 10, seed=42)


# --------------------------------------------------------- simulate_path

def test_simulate_path_one_year_positive():
    """One year at 10% annual return with 10,000/month SIP."""
    result = simulate_path(10000, 1, [0.10])
    assert isinstance(result, int)
    assert result > 120000  # must grow beyond 12 contributions


def test_simulate_path_one_year_negative():
    """One year at -20% should produce less than the sum of contributions."""
    result = simulate_path(10000, 1, [-0.20])
    assert result < 120000  # less than 12 * 10,000
    assert result > 0       # still positive (only -20%, not -100%)


def test_simulate_path_zero_return():
    """Zero annual return: corpus equals sum of contributions exactly."""
    result = simulate_path(10000, 1, [0.0])
    assert result == 120000  # 12 months * 10,000, no growth


def test_simulate_path_sequence_order_sensitivity():
    """Different ordering of the same returns should produce different corpora.

    A bad year early hurts less (less capital exposed) than a bad year late.
    This is the sequence risk the contract explicitly calls out.
    """
    # Good year first, bad year second
    corpus_good_first = simulate_path(10000, 2, [0.30, -0.30])
    # Bad year first, good year second
    corpus_bad_first = simulate_path(10000, 2, [-0.30, 0.30])
    assert corpus_good_first != corpus_bad_first


def test_simulate_path_insufficient_returns_raises():
    """Must raise if fewer annual returns than years are supplied."""
    with pytest.raises(ValueError):
        simulate_path(10000, 3, [0.10, 0.10])  # only 2, need 3


def test_simulate_path_deterministic():
    """Same inputs must produce identical results every time."""
    a = simulate_path(10000, 2, [0.10, 0.05])
    b = simulate_path(10000, 2, [0.10, 0.05])
    assert a == b


def test_simulate_path_extra_returns_ignored():
    """Extra annual returns beyond `years` are ignored, not an error."""
    result_exact = simulate_path(10000, 1, [0.10])
    result_extra = simulate_path(10000, 1, [0.10, 0.20, 0.30])
    assert result_exact == result_extra


# -------------------------------------------------------- simulate_plan

TEST_PLAN = {
    "plan_id": "T",
    "monthly_investment": 10000,
    "years": 2,
    "goal_amount": 250000,
}


def test_simulate_plan_output_shape():
    """Output must have exactly the seven §5 fields."""
    result = simulate_plan(TEST_PLAN)
    expected_keys = {
        "plan_id", "success_probability", "successful_simulations",
        "median_corpus", "p10_corpus", "p90_corpus", "p10_gap_to_goal",
    }
    assert set(result.keys()) == expected_keys


def test_simulate_plan_plan_id_preserved():
    result = simulate_plan(TEST_PLAN)
    assert result["plan_id"] == "T"


def test_simulate_plan_n_simulations_count():
    """successful_simulations must be between 0 and n_simulations."""
    result = simulate_plan(TEST_PLAN, n_simulations=10000)
    assert 0 <= result["successful_simulations"] <= 10000


def test_simulate_plan_success_consistency():
    """success_probability must equal successful_simulations / n_simulations."""
    n = 10000
    result = simulate_plan(TEST_PLAN, n_simulations=n)
    assert result["success_probability"] == result["successful_simulations"] / n


def test_simulate_plan_percentile_ordering():
    """p10 <= median <= p90."""
    result = simulate_plan(TEST_PLAN)
    assert result["p10_corpus"] <= result["median_corpus"] <= result["p90_corpus"]


def test_simulate_plan_p10_gap_formula():
    """p10_gap_to_goal = max(0, goal_amount - p10_corpus)."""
    result = simulate_plan(TEST_PLAN)
    expected_gap = max(0, TEST_PLAN["goal_amount"] - result["p10_corpus"])
    assert result["p10_gap_to_goal"] == expected_gap


def test_simulate_plan_deterministic():
    """Same seed must produce identical results."""
    a = simulate_plan(TEST_PLAN, seed=42)
    b = simulate_plan(TEST_PLAN, seed=42)
    assert a == b


def test_simulate_plan_different_seed():
    """Different seeds can produce different distributions."""
    a = simulate_plan(TEST_PLAN, seed=42)
    b = simulate_plan(TEST_PLAN, seed=999)
    # At minimum the detailed corpus percentiles should differ
    assert a["median_corpus"] != b["median_corpus"] or a["p10_corpus"] != b["p10_corpus"]


def test_simulate_plan_zero_investment():
    """Zero monthly investment must produce zero corpus and zero successes."""
    plan = {
        "plan_id": "Z",
        "monthly_investment": 0,
        "years": 2,
        "goal_amount": 100000,
    }
    result = simulate_plan(plan)
    assert result["successful_simulations"] == 0
    assert result["success_probability"] == 0.0
    assert result["median_corpus"] == 0
    assert result["p10_corpus"] == 0
    assert result["p90_corpus"] == 0
    assert result["p10_gap_to_goal"] == 100000


def test_simulate_plan_success_probability_range():
    """success_probability must be between 0.0 and 1.0."""
    result = simulate_plan(TEST_PLAN)
    assert 0.0 <= result["success_probability"] <= 1.0
