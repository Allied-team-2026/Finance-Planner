import csv
from pathlib import Path

def test_nifty_50_price_return_dataset():
    """Ensure the dataset accurately represents Nifty 50 Price Return (PR) calendar-year performance."""
    data_path = Path(__file__).resolve().parent.parent / "data" / "nifty_yearly_2005_2025.csv"
    assert data_path.exists(), f"Dataset not found at {data_path}"
    
    with open(data_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header == ["year", "annual_return"], f"Unexpected header: {header}"
        
        rows = list(reader)
        
    assert len(rows) == 21, f"Expected 21 rows, got {len(rows)}"
    
    years = []
    returns = []
    
    for r in rows:
        y = int(r[0])
        ret = float(r[1])
        years.append(y)
        returns.append(ret)
        
    # Uniqueness & Completeness
    expected_years = list(range(2005, 2026))
    assert years == expected_years, f"Years do not exactly match expected 2005-2025 range or are not sorted ascending"
    
    # Valid numeric returns test (covered by float parsing above)
    assert min(returns) > -1.0, "Annual return should be decimal, but found value <= -100%"
    assert max(returns) < 2.0, "Annual return suspiciously high for Nifty 50 decimal"
    
    # Must contain both positive and negative years (Nifty 50 PR has known drops, e.g. 2008, 2011, 2015)
    assert any(r < 0 for r in returns), "Nifty 50 PR dataset must contain negative return years"
    assert any(r > 0 for r in returns), "Nifty 50 PR dataset must contain positive return years"
    
    # Deterministic file contents check (hash-like / exact expected values test)
    # Testing specific authoritative Nifty 50 Price Return (PR) data points
    assert returns[0] == 0.3634
    assert returns[3] == -0.5179 # 2008 drop
    assert returns[-1] == 0.1050 # 2025 full calendar year final

