from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

import pytest
from orchestrator import pipeline

@pytest.fixture(autouse=True)
def enable_real_customer_engines(monkeypatch):
    # Tests normally run with all mocks. Enable just the ones we are testing here.
    monkeypatch.setattr(pipeline, "REAL_ENGINES", {"customer", "profile"})

def test_get_customer_valid_ids():
    for cid in ["C001", "C002", "C003"]:
        response = client.get(f"/api/customer/{cid}")
        assert response.status_code == 200
        data = response.json()
        assert data["customer_id"] == cid
        assert "customer_name" in data
        assert "age" in data
        assert "monthly_income" in data
        
        # Verify no leakage of private fields
        assert "transactions" not in data
        assert "ground_truth_risk" not in data
        assert "assets" not in data
        assert "liabilities" not in data
        assert "peer_cohort" not in data

def test_get_customer_unknown_id():
    response = client.get("/api/customer/UNKNOWN")
    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found"
