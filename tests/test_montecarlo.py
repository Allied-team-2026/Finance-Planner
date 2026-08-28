"""
Tests for the §5 Monte Carlo historical-return loader and resampling helper.

Does NOT test the full simulate() API, which does not exist yet.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engines.montecarlo import load_historical_returns, sample_returns  # noqa: E402
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
