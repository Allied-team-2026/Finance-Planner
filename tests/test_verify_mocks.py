import sys
import os
import types

def get_compare_dicts():
    script = os.path.join(os.path.dirname(__file__), "..", "tools", "verify_mocks.py")
    with open(script) as f:
        code = f.read()
    
    func_code = code.split("def compare_dicts(")[1].split("\ntry:")[0]
    func_code = "def compare_dicts(" + func_code
    
    mod = types.ModuleType("mock_compare")
    exec(func_code, mod.__dict__)
    return mod.compare_dicts

def test_correct_engine_mock_passes():
    compare_dicts = get_compare_dicts()
    diffs = compare_dicts({"a": 1, "b": {"c": 2.0}}, {"a": 1, "b": {"c": 2.0}})
    assert diffs == []

def test_deliberately_altered_mock_fails():
    compare_dicts = get_compare_dicts()
    diffs = compare_dicts({"a": 1}, {"a": 2}, "root")
    assert len(diffs) == 1
    assert "root.a mismatch: engine 1 != mock 2" in diffs[0]

def test_expense_volatility_mismatch():
    compare_dicts = get_compare_dicts()
    diffs = compare_dicts({"expense_volatility": 0.12}, {"expense_volatility": 0.34}, "features")
    assert len(diffs) == 1
    assert "features.expense_volatility mismatch: engine 0.12 != mock 0.34" in diffs[0]
