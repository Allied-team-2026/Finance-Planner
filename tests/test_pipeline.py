"""
Proves the orchestrator is right, using a trick the mocks make possible.

The mocks are both the input AND the expected output. So we can feed the engine
mocks in, and check what comes out equals the plan_bundle and api_response mocks
exactly - every key, every number. If the merge drops a field, renames the wrong
thing, or lets a name through to the agent payload, these tests fail.

Run: python -m pytest tests/test_pipeline.py -q
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from orchestrator.pipeline import (STAGES, build_bundle, build_response,
                                   load_mock, make_plan, run)


def stages():
    """Every engine mock, ready to feed in."""
    return {name: run(name) for name in STAGES}


def test_bundle_matches_the_mock():
    """Section 7 built from the engine mocks equals mocks/plan_bundle.json."""
    s = stages()
    built = build_bundle(s["customer"], s["profile"], s["features"], s["risk"],
                         s["plans"], s["montecarlo"], s["stress"])
    assert built == load_mock("plan_bundle.json")


def test_response_matches_the_mock():
    """Section 11 built from the engine mocks equals mocks/api_response.json."""
    s = stages()
    built = build_response(s["customer"], s["profile"], s["risk"], s["plans"],
                          s["montecarlo"], s["stress"], s["explanation"],
                          s["cohort"], s["verify"])
    expected = load_mock("api_response.json")
    built["generated_at"] = expected["generated_at"]   # today's date, not fixed
    assert built == expected


def test_no_identity_reaches_the_agents():
    """The one test that matters if it ever fails.

    Checked on the serialised payload, not on the keys, because a name can also
    arrive inside a string somebody wrote by hand.
    """
    s = stages()
    bundle = build_bundle(s["customer"], s["profile"], s["features"], s["risk"],
                          s["plans"], s["montecarlo"], s["stress"])
    text = json.dumps(bundle)
    for secret in s["customer"]["name"].split() + [s["customer"]["customer_id"]]:
        assert secret not in text, f"{secret!r} reached the agent payload"
    assert "ground_truth_risk" not in text


def test_name_comes_back_in_the_response():
    """De-identifying is only safe if the name is genuinely restored after."""
    response = make_plan("C001")
    assert response["customer_name"] == "Rahul Mehta"
    assert response["customer_id"] == "C001"


def test_rename_seam_holds():
    """Stress says `survives`; everything downstream says `survives_stress`.
    The rename happens once, in the orchestrator. This pins it."""
    s = stages()
    bundle = build_bundle(s["customer"], s["profile"], s["features"], s["risk"],
                          s["plans"], s["montecarlo"], s["stress"])
    for plan in bundle["plans"]:
        assert "survives_stress" in plan
        assert "survives" not in plan


if __name__ == "__main__":
    # Runs under pytest, and also plain `python tests/test_pipeline.py` with no
    # packages installed at all - handy on a teammate's machine mid-hackathon.
    failed = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_"):
            continue
        try:
            fn()
            print(f"pass  {name}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL  {name}: {e}")
    print(f"\n{failed} failed" if failed else "\nall tests pass")
    sys.exit(1 if failed else 0)
