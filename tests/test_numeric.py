import pytest
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agents.numeric import validate_prose_numbers, extract_decimals

def test_extract_decimals():
    text = "The value is 73.8% and cost is 2,500,000. Also -7,000."
    matches = list(extract_decimals(text))
    assert matches[0][:2] == ("73.8", 73.8)
    assert matches[1][:2] == ("2,500,000", 2500000.0)
    assert matches[2][:2] == ("-7,000", -7000.0)

def test_exact_matches():
    wl = {0.7376, 2500000.0, -7000.0}
    assert validate_prose_numbers("Value is 0.7376", wl) == []
    assert validate_prose_numbers("Cost is 2,500,000", wl) == []
    assert validate_prose_numbers("Surplus is -7,000", wl) == []

def test_percentage_presentation():
    wl = {0.7376}
    assert validate_prose_numbers("It is 73.76%", wl) == []
    assert validate_prose_numbers("It is 73.8%", wl) == []
    assert validate_prose_numbers("It is 73.8% and 0.7376", wl) == []
    
    with pytest.raises(ValueError):
        validate_prose_numbers("It is 80%", wl)
        
    wl2 = {0.42, 0.5}
    assert validate_prose_numbers("It is 42%", wl2) == []
    assert validate_prose_numbers("It is 50%", wl2) == []

def test_structural_percentiles():
    wl = {1000.0: ["payload.p10_corpus"]}
    assert validate_prose_numbers("The 10th percentile is good", wl) == []
    assert validate_prose_numbers("The p10 outcome", wl) == []
    
    with pytest.raises(ValueError):
        # 90th percentile fails because p90 doesn't exist in paths
        validate_prose_numbers("The 90th percentile is good", {1000.0: ["payload.p10"]})
