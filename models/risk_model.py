"""§3b Revealed Risk — baseline model training and evaluation.

This module trains on the six §3a features and ground_truth_risk labels.
It must never touch a raw customer record (seam rule).
"""

import json
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    classification_report,
    confusion_matrix,
)

# ── constants ───────────────────────────────────────────────────────────────

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

RANDOM_STATE = 42
TEST_SIZE = 0.2


# ── data loading ────────────────────────────────────────────────────────────

def load_dataset(path=None):
    """Load the training feature dataset and return (X, y, customer_ids).

    X is a 2-D numpy array with columns in FEATURE_ORDER.
    y is a 1-D array of string labels.
    Null avg_days_to_exit_after_drop is imputed with the training-set median
    per §3b contract.
    """
    path = path or DATA_PATH
    records = json.loads(Path(path).read_text())

    customer_ids = []
    X_raw = []
    y = []

    for r in records:
        customer_ids.append(r["customer_id"])
        row = [r["features"][k] for k in FEATURE_ORDER]
        X_raw.append(row)
        y.append(r["ground_truth_risk"])

    X = np.array(X_raw, dtype=float)
    y = np.array(y)

    # Impute null avg_days_to_exit_after_drop (column index 1) with median
    col = X[:, 1]
    median_val = np.nanmedian(col)
    nan_mask = np.isnan(col)
    col[nan_mask] = median_val

    return X, y, customer_ids


def split_data(X, y):
    """Stratified train/test split with a fixed random seed."""
    return train_test_split(
        X, y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )


# ── training ────────────────────────────────────────────────────────────────

def train_baseline(X_train, y_train):
    """Train a simple RandomForestClassifier baseline."""
    clf = RandomForestClassifier(
        n_estimators=100,
        random_state=RANDOM_STATE,
        class_weight="balanced",
    )
    clf.fit(X_train, y_train)
    return clf


# ── evaluation ──────────────────────────────────────────────────────────────

def evaluate(clf, X_test, y_test):
    """Print and return evaluation metrics."""
    y_pred = clf.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    macro_f1 = f1_score(y_test, y_pred, average="macro")
    report = classification_report(y_test, y_pred, labels=LABEL_ORDER)
    cm = confusion_matrix(y_test, y_pred, labels=LABEL_ORDER)

    print(f"Accuracy:  {acc:.4f}")
    print(f"Macro-F1:  {macro_f1:.4f}")
    print()
    print("Per-class metrics:")
    print(report)
    print("Confusion matrix (rows=true, cols=predicted):")
    print(f"{'':>15s} {'conservative':>14s} {'moderate':>14s} {'aggressive':>14s}")
    for i, label in enumerate(LABEL_ORDER):
        print(f"{label:>15s} {cm[i][0]:>14d} {cm[i][1]:>14d} {cm[i][2]:>14d}")

    return {
        "accuracy": acc,
        "macro_f1": macro_f1,
        "report": report,
        "confusion_matrix": cm,
        "y_pred": y_pred,
    }


# ── main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from collections import Counter

    X, y, _ = load_dataset()
    X_train, X_test, y_train, y_test = split_data(X, y)

    print(f"Dataset:  {len(y)} records, {X.shape[1]} features")
    print(f"Train:    {len(y_train)}  {dict(Counter(y_train))}")
    print(f"Test:     {len(y_test)}  {dict(Counter(y_test))}")
    print()

    clf = train_baseline(X_train, y_train)
    evaluate(clf, X_test, y_test)
