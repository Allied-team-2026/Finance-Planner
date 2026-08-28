"""
§5 Monte Carlo Simulation – historical-return loader and resampling helpers.

The full simulate() API will be added in a later step. This module provides:
  - load_historical_returns(): reads the Nifty 50 PR annual returns CSV
  - sample_returns(): deterministic with-replacement resampling
  - simulate_path(): single-path corpus calculation from a sampled return sequence
"""

import csv
import random
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

