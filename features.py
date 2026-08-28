"""Revealed Risk Feature Extraction Engine (Section 3a).

This module extracts deterministic behavioral and financial features from raw
customer records and profile data to feed the downstream Revealed Risk ML model.

Features Extracted (Contract Section 3a):
    1. panic_sell_count (int): Number of sell events executed during a market drawdown.
    2. avg_days_to_exit_after_drop (float): Average days taken to exit after a market drop.
    3. expense_volatility (float): Normalized monthly expense volatility (std / mean).
    4. emergency_fund_months (float): Months of expenses covered by liquid savings.
    5. equity_allocation_pct (float): Ratio of equity mutual funds to total assets.
    6. budget_overshoot_rate (float): Fraction of months where spending exceeded mean expenses.

Design Principles:
    - Pure deterministic feature extraction (no ML model dependencies here).
    - Robust null safety: missing values are imputed cleanly with 0.0 without generating NaNs.
    - Transaction deduplication across [date, category, amount].
"""

from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd


CORE_FEATURE_NAMES: List[str] = [
    "panic_sell_count",
    "avg_days_to_exit_after_drop",
    "expense_volatility",
    "emergency_fund_months",
    "equity_allocation_pct",
    "budget_overshoot_rate",
]


def clean_customer_data(raw_data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """Clean and sanitize raw customer record(s).

    Handles:
        - Null/None values in nested structures (assets, liabilities, transactions, investment_events).
        - Deduplication of identical transactions.
        - Type coercion and default filling.

    Args:
        raw_data: Single customer dict or list of customer dicts.

    Returns:
        Sanitized customer dict or list of dicts.
    """
    if isinstance(raw_data, list):
        return [clean_single_customer_data(item) for item in raw_data]
    return clean_single_customer_data(raw_data)


def clean_single_customer_data(customer: Dict[str, Any]) -> Dict[str, Any]:
    """Clean a single customer dictionary."""
    if not isinstance(customer, dict):
        raise ValueError("Customer record must be a dictionary")

    cleaned: Dict[str, Any] = {
        "customer_id": str(customer.get("customer_id", "UNKNOWN")),
        "age": int(customer.get("age", 30)) if customer.get("age") is not None else None,
        "stated_risk": str(customer.get("stated_risk", "moderate")).lower(),
        "monthly_income": float(customer.get("monthly_income") or 0.0),
        "assets": {},
        "liabilities": [],
        "transactions": [],
        "investment_events": [],
    }

    # Clean assets
    raw_assets = customer.get("assets")
    if isinstance(raw_assets, dict):
        for k, v in raw_assets.items():
            try:
                cleaned["assets"][k] = float(v) if v is not None else 0.0
            except (ValueError, TypeError):
                cleaned["assets"][k] = 0.0
    elif isinstance(raw_assets, (int, float)):
        # Fallback if scalar assets is passed
        cleaned["assets"]["savings_account"] = float(raw_assets)

    # Clean liabilities
    raw_liabilities = customer.get("liabilities")
    if isinstance(raw_liabilities, list):
        for liab in raw_liabilities:
            if isinstance(liab, dict):
                cleaned["liabilities"].append({
                    "type": str(liab.get("type", "misc")),
                    "outstanding": float(liab.get("outstanding") or 0.0),
                    "emi": float(liab.get("emi") or 0.0),
                })
    elif isinstance(raw_liabilities, (int, float)):
        cleaned["liabilities"].append({
            "type": "total",
            "outstanding": float(raw_liabilities),
            "emi": 0.0,
        })

    # Clean and deduplicate transactions
    raw_txns = customer.get("transactions")
    if isinstance(raw_txns, list) and len(raw_txns) > 0:
        seen_txns = set()
        deduped_txns = []
        for txn in raw_txns:
            if not isinstance(txn, dict):
                continue
            date_val = str(txn.get("date", "")).strip()
            cat_val = str(txn.get("category", "misc")).strip().lower()
            try:
                amt_val = float(txn.get("amount") or 0.0)
            except (ValueError, TypeError):
                amt_val = 0.0

            if amt_val <= 0.0 or not date_val:
                continue

            txn_key = (date_val, cat_val, round(amt_val, 2))
            if txn_key not in seen_txns:
                seen_txns.add(txn_key)
                deduped_txns.append({
                    "date": date_val,
                    "category": cat_val,
                    "amount": amt_val,
                })
        cleaned["transactions"] = deduped_txns

    # Clean investment events
    raw_events = customer.get("investment_events")
    if isinstance(raw_events, list):
        for ev in raw_events:
            if not isinstance(ev, dict):
                continue
            cleaned["investment_events"].append({
                "date": str(ev.get("date", "")),
                "action": str(ev.get("action", "hold")).lower(),
                "instrument": str(ev.get("instrument", "equity_mf")),
                "amount": float(ev.get("amount") or 0.0),
                "market_drawdown_pct": float(ev.get("market_drawdown_pct") or 0.0),
                "days_after_drop": float(ev.get("days_after_drop") or 0.0),
            })

    if "ground_truth_risk" in customer:
        cleaned["ground_truth_risk"] = str(customer["ground_truth_risk"]).lower()

    return cleaned


def extract_features_single(
    customer_record: Dict[str, Any],
    profile_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Union[int, float]]:
    """Extract the 6 core revealed risk features for a single customer.

    Args:
        customer_record: Raw or cleaned customer dictionary.
        profile_data: Optional pre-computed profile engine output (§2).

    Returns:
        Dict matching Section 3a features_used schema:
        {
            "panic_sell_count": int,
            "avg_days_to_exit_after_drop": float,
            "expense_volatility": float,
            "emergency_fund_months": float,
            "equity_allocation_pct": float,
            "budget_overshoot_rate": float
        }
    """
    cleaned = clean_single_customer_data(customer_record)

    # 1. Panic sell metrics
    panic_events = [
        ev for ev in cleaned["investment_events"]
        if ev["action"] == "sell" and ev["market_drawdown_pct"] > 0.0
    ]

    panic_sell_count = int(len(panic_events))
    if panic_sell_count > 0:
        avg_days_to_exit = float(np.mean([ev["days_after_drop"] for ev in panic_events]))
    else:
        avg_days_to_exit = 0.0

    # 2. Monthly expense calculation & volatility
    txns = cleaned["transactions"]
    if txns:
        txn_df = pd.DataFrame(txns)
        txn_df["date"] = pd.to_datetime(txn_df["date"], errors="coerce")
        txn_df = txn_df.dropna(subset=["date"])
        
        if not txn_df.empty:
            txn_df["year_month"] = txn_df["date"].dt.to_period("M")
            monthly_totals = txn_df.groupby("year_month")["amount"].sum()
            
            mean_expense = float(monthly_totals.mean())
            std_expense = float(monthly_totals.std(ddof=0)) if len(monthly_totals) > 1 else 0.0
            
            expense_volatility = float(std_expense / mean_expense) if mean_expense > 0 else 0.0
            overshoot_count = int((monthly_totals > mean_expense).sum())
            budget_overshoot_rate = float(overshoot_count / len(monthly_totals)) if len(monthly_totals) > 0 else 0.0
        else:
            mean_expense = 0.0
            expense_volatility = 0.0
            budget_overshoot_rate = 0.0
    else:
        mean_expense = float(profile_data.get("monthly_expense", 0.0)) if profile_data else 0.0
        expense_volatility = 0.0
        budget_overshoot_rate = 0.0

    # Override mean_expense with profile_data if provided and non-zero
    if profile_data and profile_data.get("monthly_expense"):
        mean_expense = float(profile_data["monthly_expense"])

    # 3. Emergency fund months
    savings_account = float(cleaned["assets"].get("savings_account", 0.0))
    if profile_data and "emergency_fund_months" in profile_data:
        emergency_fund_months = float(profile_data["emergency_fund_months"])
    elif mean_expense > 0:
        emergency_fund_months = float(savings_account / mean_expense)
    else:
        emergency_fund_months = 0.0

    # 4. Equity allocation percentage
    total_assets = sum(cleaned["assets"].values())
    if profile_data and profile_data.get("total_assets"):
        total_assets = float(profile_data["total_assets"])
    
    equity_mf = float(cleaned["assets"].get("equity_mf", 0.0))
    if total_assets > 0:
        equity_allocation_pct = float(equity_mf / total_assets)
    else:
        equity_allocation_pct = 0.0

    # Sanitize outputs: ensure no NaNs or Infs
    result: Dict[str, Union[int, float]] = {
        "panic_sell_count": int(panic_sell_count),
        "avg_days_to_exit_after_drop": round(float(0.0 if np.isnan(avg_days_to_exit) else avg_days_to_exit), 2),
        "expense_volatility": round(float(0.0 if np.isnan(expense_volatility) else expense_volatility), 4),
        "emergency_fund_months": round(float(0.0 if np.isnan(emergency_fund_months) else emergency_fund_months), 2),
        "equity_allocation_pct": round(float(0.0 if np.isnan(equity_allocation_pct) else equity_allocation_pct), 4),
        "budget_overshoot_rate": round(float(0.0 if np.isnan(budget_overshoot_rate) else budget_overshoot_rate), 4),
    }

    return result


def extract_features_batch(
    customer_records: List[Dict[str, Any]],
    profile_records: Optional[List[Dict[str, Any]]] = None,
) -> pd.DataFrame:
    """Extract features for multiple customer records and return a numeric feature matrix.

    Args:
        customer_records: List of customer dictionaries.
        profile_records: Optional list of corresponding profile engine outputs.

    Returns:
        pandas.DataFrame with columns CORE_FEATURE_NAMES and index customer_id.
        Guaranteed to contain zero NaNs and strictly numeric types.
    """
    rows = []
    index = []

    profile_map = {}
    if profile_records:
        for idx, prof in enumerate(profile_records):
            cid = prof.get("customer_id", f"IDX_{idx}")
            profile_map[cid] = prof

    for idx, cust in enumerate(customer_records):
        cid = str(cust.get("customer_id", f"CUST_{idx:04d}"))
        prof = profile_map.get(cid)
        features = extract_features_single(cust, profile_data=prof)
        rows.append(features)
        index.append(cid)

    df = pd.DataFrame(rows, index=index, columns=CORE_FEATURE_NAMES)
    
    # Cast datatypes explicitly
    df["panic_sell_count"] = df["panic_sell_count"].astype("int64")
    for col in [
        "avg_days_to_exit_after_drop",
        "expense_volatility",
        "emergency_fund_months",
        "equity_allocation_pct",
        "budget_overshoot_rate",
    ]:
        df[col] = df[col].astype("float64")

    # Enforce NaN/Inf freedom
    df = df.fillna(0.0).replace([np.inf, -np.inf], 0.0)
    return df


def extract_feature_matrix(
    customer_records: List[Dict[str, Any]],
    profile_records: Optional[List[Dict[str, Any]]] = None,
) -> np.ndarray:
    """Extract raw numpy 2D feature matrix (N x 6) for ML model training and inference.

    Args:
        customer_records: List of customer dictionaries.
        profile_records: Optional list of profile dictionaries.

    Returns:
        np.ndarray of shape (N, 6) with dtype float64.
    """
    df = extract_features_batch(customer_records, profile_records)
    return df.to_numpy(dtype=np.float64)
