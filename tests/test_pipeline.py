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
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from orchestrator import pipeline  # noqa: E402
from orchestrator.pipeline import (build_response, load_mock,  # noqa: E402
                                   make_plan, run_stages)


def stages():
    """Every stage's output, wired the way production wires it.

    This calls the orchestrator's own wiring instead of repeating it. An earlier
    version built the same dict with `run(name)` and no arguments, which worked
    only because mocks ignore their arguments - so the suite passed while being
    structurally incapable of testing a real engine. Repeating the wiring in a
    test is the bug, not just the missing arguments: a test with its own copy can
    keep passing after production's copy changes.
    """
    return run_stages("C001")


def test_bundle_matches_the_mock():
    """Section 7 built from the engine mocks equals mocks/plan_bundle.json."""
    assert stages()["bundle"] == load_mock("plan_bundle.json")


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
    text = json.dumps(s["bundle"])
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
    for plan in stages()["bundle"]["plans"]:
        assert "survives_stress" in plan
        assert "survives" not in plan


def test_a_real_engine_receives_the_arguments_it_expects():
    """The defect this file used to have, now pinned.

    Substitutes a recording stub for the plan generator by exactly the mechanism
    REAL_ENGINES uses, then checks what §4 was actually handed. This fails if the
    wiring passes no arguments, the wrong arguments, or them in the wrong order -
    none of which a mock can notice, because a mock ignores what it is given.

    Written as a stub rather than against the real engine on purpose: it has to
    hold now, while every stage is still a mock, or it is not a check at all.
    """
    seen = {}

    def generate(profile, risk):
        seen["profile"], seen["risk"] = profile, risk
        return load_mock("plans_out.json")

    stub = types.ModuleType("engines.plan_generator")
    stub.generate = generate
    sys.modules["engines.plan_generator"] = stub
    was_real = "plans" in pipeline.REAL_ENGINES
    pipeline.REAL_ENGINES.add("plans")
    try:
        stages()
    finally:
        # Restore, do not discard. An earlier version of this cleanup removed
        # "plans" unconditionally, so on a machine where the real engine was
        # switched on this test quietly switched it back off for everything that
        # ran after it - and the suite then reported the engine as passing when
        # it had never been called.
        if not was_real:
            pipeline.REAL_ENGINES.discard("plans")
        sys.modules.pop("engines.plan_generator", None)

    assert seen, "§4 was never called - REAL_ENGINES did not take effect"
    assert seen["profile"] == load_mock("profile_out.json")
    assert seen["risk"] == load_mock("risk_out.json")


def test_a_what_if_only_moves_the_surplus():
    """Extra savings are applied to the profile, not smuggled into an engine.

    Pins the one place a what-if is allowed to change anything, so §4 never needs
    to know what-ifs exist.
    """
    base = stages()["profile"]["monthly_surplus"]
    s = run_stages("C001", extra_monthly_savings=5000)
    assert s["profile"]["monthly_surplus"] == base + 5000
    assert load_mock("profile_out.json")["monthly_surplus"] == base


if __name__ == "__main__":
    # Runs under pytest, and also plain `python tests/test_pipeline.py` with no
    # packages installed at all - handy on a teammate's machine mid-hackathon.
    #
    # Catches Exception, not AssertionError. A wiring bug arrives as a TypeError,
    # a missing field as a KeyError, and an earlier version of this runner let
    # either one abort the whole run with a traceback instead of reporting it as
    # one failure and carrying on. A runner that only understands one kind of
    # failure hides every other kind.
    failed = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_"):
            continue
        try:
            fn()
            print(f"pass  {name}")
        except Exception as e:                     # noqa: BLE001 - see above
            failed += 1
            print(f"FAIL  {name}: {type(e).__name__}: {e}")
    print(f"\n{failed} failed" if failed else "\nall tests pass")
    sys.exit(1 if failed else 0)
