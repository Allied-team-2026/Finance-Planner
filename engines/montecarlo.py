"""
§5 Monte Carlo Simulation – historical-return loader and resampling helpers.

The full simulate() API will be added in a later step. This module provides:
  - load_historical_returns(): reads the Nifty 50 PR annual returns CSV
  - sample_returns(): deterministic with-replacement resampling
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
