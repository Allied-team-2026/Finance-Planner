import json
import pytest
from pathlib import Path

def test_plan_sizing_behavior():
    path = Path(__file__).resolve().parent.parent / "data" / "assumptions.json"
    data = json.loads(path.read_text())
    sizing = data["investment_sizing"]
    
    surpluses = [20000, 30000, 45000, 60000, 100000]
    
    prev_a, prev_b, prev_c = 0, 0, 0
    
    for s in surpluses:
        inv_a = int(round(s * sizing["Plan A"]))
        inv_b = int(round(s * sizing["Plan B"]))
        inv_c = int(round(s * sizing["Plan C"]))
        
        # Monotonicity check
        assert inv_a >= prev_a
        assert inv_b >= prev_b
        assert inv_c >= prev_c
        
        # Ordering check
        assert inv_b <= inv_a
        assert inv_a <= inv_c
        
        # C001 explicit check
        if s == 45000:
            assert inv_a == 35000
            assert inv_b == 30000
            assert inv_c == 52000
            
        prev_a, prev_b, prev_c = inv_a, inv_b, inv_c
