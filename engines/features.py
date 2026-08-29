def extract(customer, profile):
    """Extract investment-behaviour features from a customer record and profile.

    This is §3a of the contract: deterministic Python, no ML, no model imports.
    Returns only the feature vector.
    """
    investment_events = customer.get("investment_events", [])

    # panic_sell_count: sells where days_after_drop is not null
    panic_sells = [
        e for e in investment_events
        if e.get("action") == "sell" and e.get("days_after_drop") is not None
    ]
    panic_sell_count = len(panic_sells)

    # avg_days_to_exit_after_drop: mean of days_after_drop over exactly those
    # same panic sells. None when there are none — never 0.0.
    if panic_sell_count > 0:
        avg_days_to_exit_after_drop = round(
            sum(e["days_after_drop"] for e in panic_sells) / panic_sell_count, 1
        )
    else:
        avg_days_to_exit_after_drop = None

    # emergency_fund_months: copied from the Profile Engine, never recomputed
    emergency_fund_months = profile["emergency_fund_months"]

    # expense_volatility: sample stdev / mean over the last 12 monthly totals
    transactions = customer.get("transactions", [])
    if transactions:
        from statistics import stdev, mean as stat_mean
        month_totals = {}
        for t in transactions:
            m = t["date"][:7]
            month_totals[m] = month_totals.get(m, 0) + t["amount"]
        sorted_months = sorted(month_totals.keys())
        last_12 = sorted_months[-12:]
        monthly_totals = [month_totals[m] for m in last_12]
        if len(monthly_totals) >= 2:
            expense_volatility = round(stdev(monthly_totals) / stat_mean(monthly_totals), 2)
        else:
            expense_volatility = 0.0
        # budget_overshoot_rate: share of last 12 months strictly > the mean
        avg = stat_mean(monthly_totals)
        overshoot_count = sum(1 for v in monthly_totals if v > avg)
        budget_overshoot_rate = round(overshoot_count / len(monthly_totals), 2)
    else:
        expense_volatility = 0.0
        budget_overshoot_rate = 0.0

    # equity_allocation_pct: equity_mf / total_assets
    assets = customer.get("assets", {})
    total_assets = sum(assets.values())
    equity_mf = assets.get("equity_mf", 0)
    if total_assets > 0:
        equity_allocation_pct = round(equity_mf / total_assets, 4)
    else:
        equity_allocation_pct = 0.0

    return {
        "panic_sell_count": panic_sell_count,
        "avg_days_to_exit_after_drop": avg_days_to_exit_after_drop,
        "expense_volatility": expense_volatility,
        "emergency_fund_months": emergency_fund_months,
        "equity_allocation_pct": equity_allocation_pct,
        "budget_overshoot_rate": budget_overshoot_rate,
    }
