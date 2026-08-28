import json
from pathlib import Path
from engines.profile import build_profile

def test_profile_c001():
    mocks_dir = Path(__file__).parent.parent / "mocks"
    customer = json.loads((mocks_dir / "customer_C001.json").read_text())
    expected = json.loads((mocks_dir / "profile_out.json").read_text())
    
    result = build_profile(customer)
    
    for k, v in expected.items():
        if k == "_mock_note":
            continue
        assert result.get(k) == v, f"{k} mismatch: {result.get(k)} != {v}"
        
def test_risk_capacity_boundaries():
    customer = {
        "monthly_income": 100000,
        "assets": {"savings_account": 0},
        "liabilities": [],
        "goals": [{"years": 2}],
        "dependents": 3,
        "employment_type": "business_owner",
        "transactions": [{"date": "2026-07-01", "category": "rent", "amount": 90000}]
    }
    # surplus 10000 (ratio 0.1 -> 0)
    # ef = 0 -> 0
    # dep = 3 -> 0
    # goal = 2 -> 0
    # emp = biz -> 0
    # Total = 0 -> conservative
    res = build_profile(customer)
    assert res["risk_capacity"] == "conservative"
    
    # moderate = 4
    customer["assets"]["savings_account"] = 270000  # ef = 3 -> 1
    customer["employment_type"] = "salaried"  # emp = 1 -> 1
    customer["dependents"] = 1  # dep = 1 -> 1
    customer["goals"][0]["years"] = 5  # goal = 5 -> 1
    res = build_profile(customer)
    assert res["risk_capacity"] == "moderate"
    
    # aggressive = 7
    customer["transactions"][0]["amount"] = 70000 # surplus 30000 -> ratio 0.3 -> 2
    customer["assets"]["savings_account"] = 420000 # ef = 6 -> 2
    res = build_profile(customer)
    assert res["risk_capacity"] == "aggressive"

def test_expense_filtering_12_months():
    transactions = []
    # Oldest month (should be excluded)
    transactions.append({"date": "2025-06-15", "category": "rent", "amount": 100000})
    
    # 12 latest months
    for month in range(7, 13):
        transactions.append({"date": f"2025-{month:02d}-15", "category": "rent", "amount": 10000})
    for month in range(1, 7):
        transactions.append({"date": f"2026-{month:02d}-15", "category": "rent", "amount": 10000})
        
    customer = {
        "monthly_income": 50000,
        "assets": {"savings_account": 0},
        "liabilities": [],
        "goals": [],
        "dependents": 0,
        "employment_type": "salaried",
        "transactions": transactions
    }
    
    res = build_profile(customer)
    assert res["monthly_expense"] == 10000
    assert res["expense_breakdown"]["rent"] == 10000

def test_risk_capacity_minimum_reasons():
    customer = {
        "monthly_income": 100000,
        "assets": {"savings_account": 150000},
        "liabilities": [],
        "goals": [],
        "dependents": 0,
        "employment_type": "business_owner",
        "transactions": [{"date": "2026-07-01", "category": "rent", "amount": 80000}]
    }
    res = build_profile(customer)
    assert len(res["risk_capacity_reasons"]) >= 3
