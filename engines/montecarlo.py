"""
§5 Monte Carlo Simulation – historical-return loader, resampling, and
single-plan simulation.

The full multi-plan simulate() API will be added in a later step. This module
provides:
  - load_historical_returns(): reads the Nifty 50 PR annual returns CSV
  - sample_returns(): deterministic with-replacement resampling
  - simulate_path(): single-path corpus calculation from a sampled return sequence
  - simulate_plan(): run n_simulations paths for one plan and compute statistics
"""

import csv
import random
import statistics
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "nifty_yearly_2005_2025.csv"


def load_historical_returns():
    """Read data/nifty_yearly_2005_2025.csv and return observations in file order.

    Returns a list of dicts, each with integer 'year' and float 'annual_return'.
    """
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        observations = []
        for row in reader:
            observations.append({
                "year": int(row["year"]),
                "annual_return": float(row["annual_return"]),
            })
    return observations


def sample_returns(returns, n_samples, seed):
    """Sample annual returns with replacement using a deterministic seeded RNG.

    Args:
        returns: list of float annual returns (the historical observations).
        n_samples: how many samples to draw.
        seed: integer seed for reproducibility.

    Returns:
        A list of n_samples floats, each drawn from returns with replacement.

    Raises:
        ValueError: if returns is empty.
    """
    if not returns:
        raise ValueError("Cannot sample from an empty historical returns list")
    rng = random.Random(seed)
    return [rng.choice(returns) for _ in range(n_samples)]


def simulate_path(monthly_investment, years, annual_returns):
    """Calculate the final corpus for one simulated path.

    For each year, converts the sampled annual return to a monthly rate, then
    applies 12 months of SIP contributions at the start of each month followed
    by growth at that monthly rate.

    This is NOT the §4 projected_corpus formula. §4 uses a constant expected
    return; this function uses a sequence of historical annual returns that
    preserves order (capturing sequence risk).

    Args:
        monthly_investment: integer monthly SIP amount in rupees.
        years: number of years to simulate.
        annual_returns: list of floats, at least `years` long. Each element is
            one year's annual return in decimal form (e.g. 0.1050 for 10.5%).

    Returns:
        Final corpus rounded to the nearest integer rupee.

    Raises:
        ValueError: if fewer than `years` annual returns are supplied.
    """
    if len(annual_returns) < years:
        raise ValueError(
            f"Need at least {years} annual returns, got {len(annual_returns)}"
        )

    corpus = 0.0
    for year_idx in range(years):
        annual_return = annual_returns[year_idx]
        monthly_rate = (1 + annual_return) ** (1 / 12) - 1
        for _ in range(12):
            corpus += monthly_investment
            corpus *= (1 + monthly_rate)

    return round(corpus)


def _percentile(sorted_data, p):
    """Compute the p-th percentile from an already-sorted list.

    Uses linear interpolation consistent with Python's statistics module.
    """
    n = len(sorted_data)
    idx = (p / 100) * (n - 1)
    lo = int(idx)
    hi = min(lo + 1, n - 1)
    frac = idx - lo
    return round(sorted_data[lo] + frac * (sorted_data[hi] - sorted_data[lo]))


def simulate_plan(plan, historical_returns=None, n_simulations=10000, seed=42):
    """Run n_simulations Monte Carlo paths for one plan.

    Args:
        plan: dict with keys 'plan_id', 'monthly_investment', 'years',
              'goal_amount'.
        historical_returns: list of observation dicts from load_historical_returns().
            If None, loads automatically.
        n_simulations: number of simulation paths (default 10,000).
        seed: base seed for deterministic reproducibility.

    Returns:
        dict with plan_id, success_probability, successful_simulations,
        median_corpus, p10_corpus, p90_corpus, p10_gap_to_goal.
    """
    if historical_returns is None:
        historical_returns = load_historical_returns()

    returns_pool = [o["annual_return"] for o in historical_returns]
    monthly_investment = plan["monthly_investment"]
    years = plan["years"]
    goal_amount = plan["goal_amount"]

    # Use a master RNG seeded once; derive per-simulation seeds from it so
    # the entire run is deterministic for a given seed.
    master_rng = random.Random(seed)

    corpora = []
    for _ in range(n_simulations):
        sim_seed = master_rng.randint(0, 2**31 - 1)
        path_returns = sample_returns(returns_pool, years, seed=sim_seed)
        corpus = simulate_path(monthly_investment, years, path_returns)
        corpora.append(corpus)

    corpora.sort()

    successful = sum(1 for c in corpora if c >= goal_amount)

    median_corpus = _percentile(corpora, 50)
    p10_corpus = _percentile(corpora, 10)
    p90_corpus = _percentile(corpora, 90)

    return {
        "plan_id": plan["plan_id"],
        "success_probability": successful / n_simulations,
        "successful_simulations": successful,
        "median_corpus": median_corpus,
        "p10_corpus": p10_corpus,
        "p90_corpus": p90_corpus,
        "p10_gap_to_goal": max(0, goal_amount - p10_corpus),
    }

