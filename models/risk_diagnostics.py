"""§3b diagnostic — per-feature, per-class statistics for the training dataset.

This script does NOT train or tune a model.  It reports the raw feature
distributions so we can see where signal exists and where classes overlap.
"""

import json
import math
from pathlib import Path
from collections import defaultdict

FEATURE_ORDER = [
    "panic_sell_count",
    "avg_days_to_exit_after_drop",
    "expense_volatility",
    "emergency_fund_months",
    "equity_allocation_pct",
    "budget_overshoot_rate",
]

LABEL_ORDER = ["conservative", "moderate", "aggressive"]

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "training_features.json"


# ── helpers ─────────────────────────────────────────────────────────────────

def _mean(vals):
    return sum(vals) / len(vals) if vals else 0.0


def _std(vals):
    if len(vals) < 2:
        return 0.0
    m = _mean(vals)
    return math.sqrt(sum((v - m) ** 2 for v in vals) / (len(vals) - 1))


# ── core ────────────────────────────────────────────────────────────────────

def load_records(path=None):
    """Load the training feature dataset as a list of dicts."""
    path = path or DATA_PATH
    return json.loads(Path(path).read_text())


def compute_diagnostics(records):
    """Return a dict of per-feature, per-class statistics plus separability.

    Structure:
    {
      "features": {
        "<name>": {
          "overall": { "mean", "std", "min", "max", "unique", "missing" },
          "by_class": {
            "conservative": { "mean", "std", "n" },
            ...
          }
        }
      },
      "separability": [
        { "feature", "class_a", "class_b", "abs_std_mean_diff" },
        ...
      ]
    }
    """
    # Gather per-class feature values
    class_vals = {label: defaultdict(list) for label in LABEL_ORDER}
    all_vals = defaultdict(list)
    missing_counts = defaultdict(int)

    for r in records:
        label = r["ground_truth_risk"]
        for feat in FEATURE_ORDER:
            v = r["features"][feat]
            if v is None:
                missing_counts[feat] += 1
            else:
                class_vals[label][feat].append(float(v))
                all_vals[feat].append(float(v))

    # Per-feature overall + by-class stats
    features = {}
    for feat in FEATURE_ORDER:
        vals = all_vals[feat]
        overall = {
            "mean": round(_mean(vals), 4),
            "std": round(_std(vals), 4),
            "min": round(min(vals), 4) if vals else None,
            "max": round(max(vals), 4) if vals else None,
            "unique": len(set(vals)),
            "missing": missing_counts[feat],
        }
        by_class = {}
        for label in LABEL_ORDER:
            cv = class_vals[label][feat]
            by_class[label] = {
                "mean": round(_mean(cv), 4),
                "std": round(_std(cv), 4),
                "n": len(cv),
            }
        features[feat] = {"overall": overall, "by_class": by_class}

    # Pairwise standardized mean differences
    separability = []
    for feat in FEATURE_ORDER:
        pooled_std = features[feat]["overall"]["std"]
        if pooled_std == 0:
            continue
        for i, a in enumerate(LABEL_ORDER):
            for b in LABEL_ORDER[i + 1:]:
                diff = abs(
                    features[feat]["by_class"][a]["mean"]
                    - features[feat]["by_class"][b]["mean"]
                )
                separability.append({
                    "feature": feat,
                    "class_a": a,
                    "class_b": b,
                    "abs_std_mean_diff": round(diff / pooled_std, 4),
                })

    separability.sort(key=lambda x: x["abs_std_mean_diff"], reverse=True)

    return {"features": features, "separability": separability}


def print_report(diag):
    """Print a human-readable diagnostic report."""
    features = diag["features"]

    # ── Feature summary table ───────────────────────────────────────────
    print("=" * 90)
    print("FEATURE SUMMARY")
    print("=" * 90)
    hdr = f"{'Feature':<35s} {'Mean':>8s} {'Std':>8s} {'Min':>8s} {'Max':>8s} {'Uniq':>6s} {'Miss':>6s}"
    print(hdr)
    print("-" * 90)
    for feat in FEATURE_ORDER:
        o = features[feat]["overall"]
        print(
            f"{feat:<35s} {o['mean']:>8.4f} {o['std']:>8.4f} "
            f"{o['min']:>8.4f} {o['max']:>8.4f} {o['unique']:>6d} {o['missing']:>6d}"
        )

    # ── Per-class means ─────────────────────────────────────────────────
    print()
    print("=" * 90)
    print("PER-CLASS MEANS")
    print("=" * 90)
    hdr = f"{'Feature':<35s} {'conservative':>14s} {'moderate':>14s} {'aggressive':>14s}"
    print(hdr)
    print("-" * 90)
    for feat in FEATURE_ORDER:
        bc = features[feat]["by_class"]
        print(
            f"{feat:<35s} "
            f"{bc['conservative']['mean']:>14.4f} "
            f"{bc['moderate']['mean']:>14.4f} "
            f"{bc['aggressive']['mean']:>14.4f}"
        )

    # ── Per-class standard deviations ───────────────────────────────────
    print()
    print("=" * 90)
    print("PER-CLASS STANDARD DEVIATIONS")
    print("=" * 90)
    print(hdr)
    print("-" * 90)
    for feat in FEATURE_ORDER:
        bc = features[feat]["by_class"]
        print(
            f"{feat:<35s} "
            f"{bc['conservative']['std']:>14.4f} "
            f"{bc['moderate']['std']:>14.4f} "
            f"{bc['aggressive']['std']:>14.4f}"
        )

    # ── Top separability pairs ──────────────────────────────────────────
    print()
    print("=" * 90)
    print("TOP 10 CLASS-SEPARATING FEATURE PAIRS (abs standardized mean diff)")
    print("=" * 90)
    print(f"{'Feature':<35s} {'Class A':<14s} {'Class B':<14s} {'|d|/σ':>8s}")
    print("-" * 90)
    for entry in diag["separability"][:10]:
        print(
            f"{entry['feature']:<35s} "
            f"{entry['class_a']:<14s} "
            f"{entry['class_b']:<14s} "
            f"{entry['abs_std_mean_diff']:>8.4f}"
        )

    # ── Interpretation ──────────────────────────────────────────────────
    if diag["separability"]:
        top = diag["separability"][0]
        print()
        print(f"Strongest separator: {top['feature']} between "
              f"{top['class_a']} and {top['class_b']} "
              f"(|d|/σ = {top['abs_std_mean_diff']:.4f})")
    print()


# ── main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    records = load_records()
    diag = compute_diagnostics(records)
    print_report(diag)
