"""
Tests for data/shock_events.json – the §6 Stress Test shock event library.

Validates structure, uniqueness, probability bounds, and cash-impact format.
Does NOT test stress-test calculations, which do not exist yet.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DATA_PATH = ROOT / "data" / "shock_events.json"

REQUIRED_FIELDS = {"event_id", "label", "annual_probability", "cash_impact"}

REQUIRED_EVENT_IDS = {"appraisal_miss", "medical_expense", "rent_hike", "job_loss_3m"}


def _load():
    return json.loads(DATA_PATH.read_text())


# ---------------------------------------------------------------- structure

def test_file_exists():
    assert DATA_PATH.exists(), f"{DATA_PATH} not found"


def test_valid_json():
    """File must parse as valid JSON."""
    events = _load()
    assert isinstance(events, list)


def test_exactly_ten_events():
    events = _load()
    assert len(events) == 10


def test_required_event_ids_present():
    events = _load()
    ids = {e["event_id"] for e in events}
    assert REQUIRED_EVENT_IDS.issubset(ids)


def test_event_ids_unique():
    events = _load()
    ids = [e["event_id"] for e in events]
    assert len(ids) == len(set(ids))


def test_each_event_has_exactly_required_fields():
    """No missing fields, no unexpected fields."""
    events = _load()
    for e in events:
        assert set(e.keys()) == REQUIRED_FIELDS, (
            f"Event {e.get('event_id', '?')} has keys {set(e.keys())}, "
            f"expected {REQUIRED_FIELDS}"
        )


# ----------------------------------------------------------------- values

def test_labels_are_nonempty_strings():
    events = _load()
    for e in events:
        assert isinstance(e["label"], str)
        assert len(e["label"].strip()) > 0


def test_annual_probability_in_valid_range():
    events = _load()
    for e in events:
        p = e["annual_probability"]
        assert isinstance(p, (int, float))
        assert 0.0 <= p <= 1.0, (
            f"Event {e['event_id']} probability {p} out of [0.0, 1.0]"
        )


def test_cash_impact_is_integer_rupees():
    events = _load()
    for e in events:
        ci = e["cash_impact"]
        assert isinstance(ci, int), (
            f"Event {e['event_id']} cash_impact {ci} is not an integer"
        )


def test_cash_impact_is_negative():
    """Shock events represent adverse cash impacts."""
    events = _load()
    for e in events:
        assert e["cash_impact"] < 0, (
            f"Event {e['event_id']} cash_impact {e['cash_impact']} is not negative"
        )


# -------------------------------------------------------- specific events

def test_appraisal_miss_values():
    events = _load()
    e = next(ev for ev in events if ev["event_id"] == "appraisal_miss")
    assert e["annual_probability"] == 0.23
    assert e["cash_impact"] == -180000


def test_medical_expense_values():
    events = _load()
    e = next(ev for ev in events if ev["event_id"] == "medical_expense")
    assert e["annual_probability"] == 0.10
    assert e["cash_impact"] == -200000


def test_rent_hike_values():
    events = _load()
    e = next(ev for ev in events if ev["event_id"] == "rent_hike")
    assert e["annual_probability"] == 0.30
    assert e["cash_impact"] == -120000


# --------------------------------------------------------- deterministic

def test_deterministic_load():
    """Repeated loads must return identical data."""
    a = _load()
    b = _load()
    assert a == b


import math

def test_combination_count_is_165():
    """Prove that C(10,2) + C(10,3) = 165"""
    events = _load()
    n = len(events)
    assert n == 10
    c_2 = math.comb(n, 2)
    c_3 = math.comb(n, 3)
    assert c_2 == 45
    assert c_3 == 120
    assert c_2 + c_3 == 165
