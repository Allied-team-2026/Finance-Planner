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
    expected = load_mock("plan_bundle.json")
    expected["peer_cohort"] = load_mock("peer_cohort_out.json")
    assert stages()["bundle"] == expected


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


def test_privacy_boundary_in_response():
    """Ensure the final API response does not expose customer_id or customer_name."""
    response = make_plan("C001")
    assert "customer_name" not in response
    assert "customer_id" not in response


def test_rename_seam_holds():
    """Stress says `survives`; everything downstream says `survives_stress`.
    The rename happens once, in the orchestrator. This pins it."""
    for plan in stages()["bundle"]["plans"]:
        assert "survives_stress" in plan
        assert "survives" not in plan


def arguments_handed_to(stage, target, mock_file, **what_if):
    """Run the pipeline with one stage swapped for a stub that records its input.

    Swaps it by exactly the mechanism REAL_ENGINES uses, so this catches wiring
    that passes no arguments, the wrong ones, or them in the wrong order - none of
    which a mock can notice, because a mock ignores what it is given. Callers
    unpack the result, so the unpack is itself the check on how many arguments the
    stage was handed.

    Written against a stub rather than a real engine on purpose: it has to hold
    now, while every stage is still a mock, or it is not a check at all.
    """
    module_name, function_name = target.split(":")
    seen = []

    def record(*args):
        seen.append(args)
        return load_mock(mock_file)

    stub = types.ModuleType(module_name)
    setattr(stub, function_name, record)
    sys.modules[module_name] = stub
    was_real = stage in pipeline.REAL_ENGINES
    pipeline.REAL_ENGINES.add(stage)
    try:
        run_stages("C001", **what_if)
    finally:
        # Restore, do not discard. An earlier version of this cleanup removed the
        # stage unconditionally, so on a machine where the real engine was
        # switched on it quietly switched it back off for everything that ran
        # after it - and the suite then reported the engine as passing when it had
        # never been called.
        if not was_real:
            pipeline.REAL_ENGINES.discard(stage)
        sys.modules.pop(module_name, None)

    assert seen, f"{stage} was never called - REAL_ENGINES did not take effect"
    return seen[0]


def test_a_real_engine_receives_the_arguments_it_expects():
    """The defect this file used to have, now pinned. §4 takes profile, risk, goals."""
    profile, risk, goals = arguments_handed_to("plans", "engines.plan_generator:generate",
                                        "plans_out.json")
    assert profile == load_mock("profile_out.json")
    assert risk == load_mock("risk_out.json")
    assert goals == load_mock("customer_C001.json").get("goals", [])


def test_c001_real_profile_features_risk_plans_chain():
    """Integration test activating real profile -> features -> risk -> plans chain."""
    real_stages = {"profile", "features", "risk", "plans"}
    original_real_engines = set(pipeline.REAL_ENGINES)
    pipeline.REAL_ENGINES.update(real_stages)
    try:
        # Capture engine status to verify active set
        status = pipeline.engine_status()
        for st in real_stages:
            assert status[st] == "engine"
        
        # Run pipeline
        s = pipeline.run_engines("C001")
        
        # Verify Risk
        risk = s["risk"]
        assert risk["stated_risk"] == "aggressive"
        assert risk["revealed_risk"] == "moderate"
        assert risk["mismatch"] is True
        
        # Verify Plans
        plans = s["plans"]["plans"]
        assert len(plans) == 3
        
        plan_by_id = {p["plan_id"]: p for p in plans}
        assert plan_by_id["A"]["monthly_investment"] == 35000
        assert plan_by_id["B"]["monthly_investment"] == 30000
        assert plan_by_id["C"]["monthly_investment"] == 52000
        
        assert plan_by_id["C"]["feasible"] is False
        assert plan_by_id["C"]["shortfall"] == 7000
        assert plan_by_id["C"]["exceeds_risk_ceiling"] is True
    finally:
        pipeline.REAL_ENGINES.clear()
        pipeline.REAL_ENGINES.update(original_real_engines)


def test_c001_real_profile_through_montecarlo_chain():
    """Integration test activating real profile -> features -> risk -> plans -> montecarlo."""
    real_stages = {"profile", "features", "risk", "plans", "montecarlo"}
    original_real_engines = set(pipeline.REAL_ENGINES)
    pipeline.REAL_ENGINES.update(real_stages)
    try:
        # Verify only the five stages are engines
        status = pipeline.engine_status()
        for st in real_stages:
            assert status[st] == "engine"
        for st in ("stress", "cohort", "explanation", "challenge", "verify"):
            assert status[st] == "mock"

        s = pipeline.run_engines("C001")
        mc = s["montecarlo"]

        # Top-level structure
        assert mc["n_simulations"] == 10000
        assert mc["returns_data_source"] == "nifty_yearly_2005_2025.csv"
        assert len(mc["results"]) == 3

        # Plan order preserved
        ids = [r["plan_id"] for r in mc["results"]]
        assert ids == ["A", "B", "C"]

        # Per-plan validation
        for r in mc["results"]:
            assert 0.0 <= r["success_probability"] <= 1.0
            assert 0 <= r["successful_simulations"] <= 10000
            assert r["success_probability"] == r["successful_simulations"] / 10000
            assert r["p10_corpus"] <= r["median_corpus"] <= r["p90_corpus"]
            assert r["p10_gap_to_goal"] >= 0
            assert r["p10_gap_to_goal"] == max(0, 2500000 - r["p10_corpus"])
    finally:
        pipeline.REAL_ENGINES.clear()
        pipeline.REAL_ENGINES.update(original_real_engines)


def test_c001_real_profile_through_stress_chain():
    """Integration test activating real profile -> features -> risk -> plans -> montecarlo -> stress."""
    real_stages = {"profile", "features", "risk", "plans", "montecarlo", "stress"}
    original_real_engines = set(pipeline.REAL_ENGINES)
    pipeline.REAL_ENGINES.update(real_stages)
    try:
        # Verify only the six stages are engines
        status = pipeline.engine_status()
        for st in real_stages:
            assert status[st] == "engine"
        for st in ("customer", "cohort", "explanation", "challenge", "verify"):
            assert status[st] == "mock"

        s = pipeline.run_engines("C001")
        
        # 1. Verify the real Stress Test produces three results, one each for A/B/C.
        stress = s["stress"]
        assert "results" in stress
        assert len(stress["results"]) == 3
        ids = [r["plan_id"] for r in stress["results"]]
        assert ids == ["A", "B", "C"]
        
        # 2. Verify every stress result contains the 5 required fields and 165 combos
        for r in stress["results"]:
            assert "survives" in r
            assert "breaking_combo" in r
            assert "breaking_probability" in r
            assert "shortfall_if_hit" in r
            assert r["combos_tested"] == 165
        
        # 3. Verify the orchestrator merges each stress result into the corresponding plan
        bundle_plans = s["bundle"]["plans"]
        assert len(bundle_plans) == 3
        
        for plan in bundle_plans:
            # 4. Verify the orchestrator renames survives -> survives_stress
            assert "survives_stress" in plan
            assert "survives" not in plan
            
            # 5. Verify the Monte Carlo fields remain intact
            assert "success_probability" in plan
            assert "median_corpus" in plan
            assert "p10_corpus" in plan
            
            # Additional stress merge fields
            assert "breaking_combo" in plan
            assert "breaking_probability" in plan
            assert "shortfall_if_hit" in plan

    finally:
        pipeline.REAL_ENGINES.clear()
        pipeline.REAL_ENGINES.update(original_real_engines)


def test_c001_real_profile_through_cohort_chain():
    """Integration test activating real profile -> features -> risk -> plans -> montecarlo -> stress -> cohort."""
    real_stages = {"profile", "features", "risk", "plans", "montecarlo", "stress", "cohort"}
    original_real_engines = set(pipeline.REAL_ENGINES)
    pipeline.REAL_ENGINES.update(real_stages)
    try:
        # Verify only the seven stages are engines
        status = pipeline.engine_status()
        for st in real_stages:
            assert status[st] == "engine"
        for st in ("customer", "explanation", "challenge", "verify"):
            assert status[st] == "mock"

        s = pipeline.run_engines("C001")
        
        cohort = s["cohort"]
        
        # 1. Verify Cohort has all 12 contract fields
        expected_fields = {
            "cohort_size", "matched_on", "age_band", "income_band", "goal_type",
            "median_monthly_surplus", "median_savings_rate", "customer_savings_rate",
            "savings_rate_percentile", "mismatch_rate", "most_common_plan_label",
            "most_common_allocation"
        }
        assert set(cohort.keys()) == expected_fields
        
        # 2. Verify C001 actual output values
        assert cohort["cohort_size"] == 20
        assert cohort["matched_on"] == ["age_band", "income_band"]
        assert cohort["age_band"] == "26-30"
        assert cohort["income_band"] == "100000-150000"
        assert cohort["goal_type"] == "house_downpayment"
        assert cohort["customer_savings_rate"] == 0.375
        assert cohort["savings_rate_percentile"] == 50.0
        assert cohort["mismatch_rate"] == 0.75
        assert cohort["most_common_plan_label"] == "Steady"
        assert cohort["most_common_allocation"] == {"debt": 0.6, "equity": 0.4}
        
        # 3. Verify privacy (no identifier)
        cohort_json = json.dumps(cohort)
        assert "Jane" not in cohort_json
        assert "C001" not in cohort_json
        assert "peer_" not in cohort_json

    finally:
        pipeline.REAL_ENGINES.clear()
        pipeline.REAL_ENGINES.update(original_real_engines)


def test_null_cohort_preservation():
    """Verify that a None cohort doesn't crash the orchestrator."""
    real_stages = {"profile", "features", "risk", "plans", "montecarlo", "stress", "cohort"}
    original_real_engines = set(pipeline.REAL_ENGINES)
    pipeline.REAL_ENGINES.update(real_stages)
    try:
        # We can force a None cohort return by monkeypatching generate_dataset to return empty
        import engines.peer_cohort
        old_match = engines.peer_cohort.match_cohort
        engines.peer_cohort.match_cohort = lambda *args, **kwargs: None
        
        s = pipeline.run_engines("C001")
        assert s["cohort"] is None
        
        engines.peer_cohort.match_cohort = old_match
    finally:
        pipeline.REAL_ENGINES.clear()
        pipeline.REAL_ENGINES.update(original_real_engines)


def test_real_plan_generator_activation():
    """Activate the real plan generator and ensure it works with the goals passed from the pipeline."""
    was_real = "plans" in pipeline.REAL_ENGINES
    pipeline.REAL_ENGINES.add("plans")
    try:
        s = run_stages("C001")
        plans = s["plans"]["plans"]
        assert len(plans) == 3
        plan_ids = {p["plan_id"] for p in plans}
        assert plan_ids == {"A", "B", "C"}
    finally:
        if not was_real:
            pipeline.REAL_ENGINES.discard("plans")


def test_features_is_handed_the_profile_the_contract_promises_it():
    """§3a takes the customer record AND the profile - contract line 276.

    The wiring passed only the customer until 27 Aug, which no mock could notice.
    Saurabh caught it while reading the contract against the code, before writing
    a line of §3a.

    Runs with a what-if on purpose. §3a must see the real profile, not the
    inflated one: revealed risk describes what this customer has already done, so
    a hypothetical 5,000 a month must not be able to move the risk prediction.
    """
    customer, profile = arguments_handed_to("features", "engines.features:extract",
                                            "features_out.json",
                                            extra_monthly_savings=5000)
    assert customer == load_mock("customer_C001.json")
    assert profile == load_mock("profile_out.json")


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
import os
import json
import pytest
from orchestrator import pipeline
from orchestrator.pipeline import load_mock, make_challenge

def test_make_challenge_integration():
    """Verify that make_challenge correctly integrates explanation, verification, and chosen_plan_id."""
    was_real = "challenge" in pipeline.REAL_ENGINES
    pipeline.REAL_ENGINES.discard("challenge")
    try:
        # We need to spy on run("challenge", ...)
        original_run = pipeline.run
        captured_args = []
        
        def spy_run(stage, *args):
            if stage == "challenge":
                captured_args.extend(args)
                return load_mock("challenge_out.json")
            return original_run(stage, *args)
            
        pipeline.run = spy_run
        try:
            result = make_challenge("C001", "B")
            assert len(captured_args) == 4
            bundle, expl, verif, plan_id = captured_args
            assert plan_id == "B"
            assert "monthly_surplus" in bundle["profile"]
            assert "plans_text" in expl
            assert "status" in verif
            
            # test privacy on final output
            result_str = json.dumps(result)
            assert "C001" not in result_str
            assert "Rahul" not in result_str
        finally:
            pipeline.run = original_run
    finally:
        if was_real:
            pipeline.REAL_ENGINES.add("challenge")

@pytest.mark.skipif(not os.environ.get("GROQ_API_KEY"), reason="live")
def test_live_c001_agent_chain():
    """End-to-End live test exactly once without retries."""
    real_stages = {"profile", "features", "risk", "plans", "montecarlo", "stress", "cohort", "explanation", "verify", "challenge"}
    original_real_engines = set(pipeline.REAL_ENGINES)
    pipeline.REAL_ENGINES.update(real_stages)
    try:
        s = pipeline.run_stages("C001")
        
        bundle = s["bundle"]
        expl = s["explanation"]
        verif = s["verify"]
        
        # Make a challenge for plan C
        chall = pipeline.run("challenge", bundle, expl, verif, "C")
        
        print("\n--- LIVE C001 AGENT CHAIN OUTPUT ---")
        print("CHOSEN_PLAN_ID: C")
        print("\nEXPLANATION OUTPUT:")
        print(json.dumps(expl, indent=2))
        print("\nVERIFIER RESULT:")
        print(json.dumps(verif, indent=2))
        print("\nCHALLENGER OUTPUT:")
        print(json.dumps(chall, indent=2))
        
        # Check Privacy
        final_str = json.dumps({"expl": expl, "verif": verif, "chall": chall}).lower()
        assert "c001" not in final_str
        assert "rahul mehta" not in final_str
        assert "ground_truth_risk" not in final_str
        
        # Check factuality indicator
        assert chall["chosen_plan_id"] == "C"
        
    finally:
        pipeline.REAL_ENGINES.clear()
        pipeline.REAL_ENGINES.update(original_real_engines)
