import json
import math
from pathlib import Path

from engines.profile import build_profile
from engines.features import extract
from engines.synthetic_data import generate_dataset
from models.risk_model import predict, load_dataset, FEATURE_ORDER

def distance(f1, f2):
    """Simple Euclidean distance between two feature dicts/lists."""
    d = 0.0
    for i, k in enumerate(FEATURE_ORDER):
        v1 = f1[k] if isinstance(f1, dict) else f1[i]
        v2 = f2[k] if isinstance(f2, dict) else f2[i]
        
        # impute nulls with a fixed value for distance calculation
        if v1 is None: v1 = 5.5
        if v2 is None: v2 = 5.5
            
        d += (float(v1) - float(v2)) ** 2
    return math.sqrt(d)

def run_diagnostic():
    # 1. Load C001
    c001_path = Path(__file__).resolve().parent.parent / "mocks" / "customer_C001.json"
    c001 = json.loads(c001_path.read_text())
    
    p001 = build_profile(c001)
    f001 = extract(c001, p001)
    pred_001 = predict(f001, "aggressive")
    
    print("=== C001 DIAGNOSTIC ===")
    print("C001 Features:")
    for k in FEATURE_ORDER:
        print(f"  {k}: {f001[k]}")
    print(f"\nPrediction: {pred_001['revealed_risk']} (Confidence: {pred_001['confidence']})")
    
    # 2. Synthetic Customer with Full History
    synth = generate_dataset(1, 42)[0]
    p_syn = build_profile(synth)
    f_syn = extract(synth, p_syn)
    pred_syn = predict(f_syn, "aggressive")
    
    print("\n=== SYNTHETIC CUSTOMER DIAGNOSTIC (Full History) ===")
    print("Features:")
    for k in FEATURE_ORDER:
        print(f"  {k}: {f_syn[k]:.4f}" if isinstance(f_syn[k], float) else f"  {k}: {f_syn[k]}")
    print(f"\nPrediction: {pred_syn['revealed_risk']} (Confidence: {pred_syn['confidence']})")
    
    # 3. Nearest neighbors in training set
    X, y, _ = load_dataset()
    
    distances = []
    for i in range(len(X)):
        d = distance(f001, X[i])
        distances.append((d, i, y[i], X[i]))
        
    distances.sort(key=lambda x: x[0])
    
    print("\n=== NEAREST TRAINING EXAMPLES ===")
    for i in range(3):
        d, idx, label, row = distances[i]
        print(f"Neighbor {i+1} (Dist: {d:.2f}): Label -> {label}")
        print(f"  Features: {list(row)}")

    print("\n=== CONCLUSION ===")
    if f001["expense_volatility"] == 0 and f001["budget_overshoot_rate"] == 0:
        print("C001 predicts 'conservative' primarily because its 1-month mock history")
        print("yields 0 volatility and 0 overshoot. The model relies heavily on ")
        print("the 24-month variance seen in synthetic data. When these features collapse ")
        print("to 0, the model assigns the record to a conservative cluster despite")
        print("equity allocation or panic sell counts.")
        
    return {
        "c001_features": f001,
        "c001_prediction": pred_001,
        "synth_features": f_syn,
        "synth_prediction": pred_syn
    }

if __name__ == "__main__":
    run_diagnostic()
