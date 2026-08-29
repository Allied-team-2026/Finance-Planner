import sys
from pathlib import Path
import json
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from orchestrator.pipeline import run_engines, REAL_ENGINES
from agents.explanation import fallback_explain
from agents.verifier import verify

def test_fallback_passes_real_verifier():
    """Proves the actual fallback text passes the actual Verifier using real engine outputs."""
    
    # 1. Build a real C001 bundle using current real engines
    original_real_engines = set(REAL_ENGINES)
    REAL_ENGINES.update({"profile", "features", "risk", "plans", "montecarlo", "stress", "cohort"})
    
    try:
        s = run_engines("C001")
        bundle = s["bundle"]
        
        # 2. Call fallback_explain(bundle)
        fallback_expl = fallback_explain(bundle)
        
        # 3. Pass fallback directly into the REAL verify
        verification = verify(fallback_expl, bundle)
        
        # 4. Assert status == "pass"
        assert verification["status"] == "pass", f"Verification failed: {verification}"
        
        # 5. Assert unverified_numbers == []
        assert verification["unverified_numbers"] == []
        
        # 6. Assert no privacy violations
        fallback_str = json.dumps(fallback_expl).lower()
        forbidden = ["c001", "rahul", "mehta", "ground_truth_risk", "raw transaction", "investment_event"]
        for term in forbidden:
            assert term not in fallback_str, f"Privacy violation: found '{term}' in fallback output."
            
    finally:
        REAL_ENGINES.clear()
        REAL_ENGINES.update(original_real_engines)
