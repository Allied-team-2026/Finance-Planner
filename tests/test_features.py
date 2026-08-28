import json
from pathlib import Path
from engines.features import extract

MOCKS = Path(__file__).parent.parent / "mocks"


def test_c001_features():
    """C001 must produce all six fields, matching the mock where data supports it."""
    customer = json.loads((MOCKS / "customer_C001.json").read_text())
    profile = json.loads((MOCKS / "profile_out.json").read_text())

    result = extract(customer, profile)

    assert result["panic_sell_count"] == 2
    assert result["avg_days_to_exit_after_drop"] == 3.0
    assert result["emergency_fund_months"] == 0.4
    # equity_allocation_pct: 400000 / 800000 = 0.5
    assert result["equity_allocation_pct"] == 0.5
    # expense_volatility and budget_overshoot_rate need 12 months of data;
    # C001 mock has only 1 month, so we cannot match the mock values here.
    # We verify the fields exist and are the right type.
    assert isinstance(result["expense_volatility"], float)
    assert isinstance(result["budget_overshoot_rate"], float)


def test_zero_panic_sells():
    """A customer with no panic sells gets count 0 and avg None."""
    customer = {
        "investment_events": [
            {"action": "buy", "instrument": "equity_mf", "amount": 50000,
             "market_drawdown_pct": 0.0, "days_after_drop": None},
        ],
        "transactions": [],
        "assets": {},
    }
    profile = {"emergency_fund_months": 3.0}

    result = extract(customer, profile)

    assert result["panic_sell_count"] == 0
    assert result["avg_days_to_exit_after_drop"] is None
    assert result["emergency_fund_months"] == 3.0


def test_calm_market_sell_excluded():
    """A sell in a calm market (days_after_drop is null) must not count."""
    customer = {
        "investment_events": [
            # calm-market sell — not a panic sell
            {"action": "sell", "instrument": "equity_mf", "amount": 100000,
             "market_drawdown_pct": 0.0, "days_after_drop": None},
            # genuine panic sell
            {"action": "sell", "instrument": "equity_mf", "amount": 80000,
             "market_drawdown_pct": 7.0, "days_after_drop": 5},
        ],
        "transactions": [],
        "assets": {},
    }
    profile = {"emergency_fund_months": 1.2}

    result = extract(customer, profile)

    assert result["panic_sell_count"] == 1
    assert result["avg_days_to_exit_after_drop"] == 5.0
    assert result["emergency_fund_months"] == 1.2


def test_12_month_expense_statistics():
    """Deterministic 12-month fixture with hand-calculated expected values.

    Monthly totals: [80, 120, 80, 120, 80, 120, 80, 120, 80, 120, 80, 120] (* 1000)
    Mean = 100000.  stdev (sample, n-1) of [80k,120k]*6 = sqrt( (12 * 400000000) / 11 )
                   = sqrt(436363636.36...) ≈ 20892.  20892 / 100000 ≈ 0.21
    Overshoot: 6 months > 100000 (the 120k months). 6/12 = 0.50
    """
    from statistics import stdev, mean as stat_mean

    transactions = []
    for i in range(12):
        month = i + 1
        year = 2026 if month <= 6 else 2025
        m = month if month <= 6 else month - 6 + 6  # 7..12 for 2025, 1..6 for 2026
        if month <= 6:
            date = f"2026-{month:02d}-15"
        else:
            date = f"2025-{(month):02d}-15"
        amount = 80000 if i % 2 == 0 else 120000
        transactions.append({"date": date, "category": "rent", "amount": amount})

    customer = {
        "investment_events": [],
        "transactions": transactions,
        "assets": {"equity_mf": 300000, "fixed_deposit": 200000},
    }
    profile = {"emergency_fund_months": 2.0}

    result = extract(customer, profile)

    # Hand-verify: stdev([80k,120k,80k,...]) / mean = ~0.21
    monthly_totals = [80000, 120000] * 6
    expected_vol = round(stdev(monthly_totals) / stat_mean(monthly_totals), 2)
    assert result["expense_volatility"] == expected_vol

    # 6 of 12 months are > mean (the 120k months)
    assert result["budget_overshoot_rate"] == 0.50

    # equity: 300000 / 500000 = 0.6
    assert result["equity_allocation_pct"] == 0.6

