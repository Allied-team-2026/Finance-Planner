"""Every customer against every plan, on the real engines and the real LLM.

The bug that reached the screen was C001's 52,000 shown to C002. No test caught
it because no test ran more than one customer, and the by-hand walkthrough is
nine clicks nobody does twice. This is those nine clicks, as one command:

    python tools/live_matrix.py

It spends real Groq tokens on purpose - three plan runs and nine challenges -
because the failures worth finding only appear when the model is really writing
the text. Exits non-zero if anything is wrong, so it can gate a demo.

Run it once before demo day and once after any change to an agent prompt.
"""

import math
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.numeric import extract_numbers_with_paths
from orchestrator.pipeline import make_challenge, make_plan, run_engines

CUSTOMERS = ["C001", "C002", "C003"]
PLANS = ["A", "B", "C"]

# The fields the UI paints a colour from. A null here is the colour bug: in
# JavaScript `null >= 0` is false, so a missing number silently renders red.
MUST_NOT_BE_NULL = ["monthly_investment", "success_probability",
                    "projected_corpus", "survives_stress"]

failures = []


def check(ok, label):
    print(f"  {'ok  ' if ok else 'FAIL'} {label}")
    if not ok:
        failures.append(label)


def in_bundle(value, allowed):
    """The verifier's rule: a number must be one the engines produced."""
    return any(math.isclose(float(value), a, rel_tol=1e-5, abs_tol=1e-5)
               for a in allowed)


def check_plan_response(cid, response, allowed):
    check(response["customer_id"] == cid,
          f"{cid}: response is for the customer we asked about")
    check(bool(response["customer_name"]),
          f"{cid}: name came back after the agents ran")
    check(len(response["plans"]) == 3, f"{cid}: three plans")

    for plan in response["plans"]:
        pid = plan["plan_id"]
        for field in MUST_NOT_BE_NULL:
            check(plan.get(field) is not None,
                  f"{cid} plan {pid}: {field} is not null")
        check(in_bundle(plan["monthly_investment"], allowed),
              f"{cid} plan {pid}: monthly_investment is this customer's number")
        # Affordability drives the red/green badge, so the flag and the
        # arithmetic have to agree. The UI must never decide this itself.
        surplus = response["profile"]["monthly_surplus"]
        check(plan["feasible"] == (plan["monthly_investment"] <= surplus),
              f"{cid} plan {pid}: feasible flag agrees with surplus")

    check(response["verifier"]["status"] == "pass",
          f"{cid}: verifier passed the explanation "
          f"({response['verifier']['unverified_numbers']}"
          f"{response['verifier']['suitability_flags']})")


def check_challenge(cid, pid, response, allowed):
    ch = response["challenge"]
    check(ch is not None, f"{cid} plan {pid}: a challenge came back")
    if ch is None:
        return

    check(ch["chosen_plan_id"] == pid,
          f"{cid} plan {pid}: challenge is about the plan we asked about")
    check(ch["alternative_suggested"] in PLANS and
          ch["alternative_suggested"] != pid,
          f"{cid} plan {pid}: suggests a real, different plan")

    for num in ch.get("numbers_used", []):
        check(in_bundle(num, allowed),
              f"{cid} plan {pid}: challenge number {num} is this customer's")

    check(response["verifier"]["status"] == "pass",
          f"{cid} plan {pid}: verifier passed explanation and challenge "
          f"({response['verifier']['unverified_numbers']}"
          f"{response['verifier']['suitability_flags']})")


def main():
    if not os.environ.get("GROQ_API_KEY"):
        sys.exit("GROQ_API_KEY is not set, so there is nothing live to test.")

    for cid in CUSTOMERS:
        # The agent payload for this customer, used as the whitelist. Anything
        # the screen shows that is not in here came from somewhere it shouldn't.
        bundle = run_engines(cid)["bundle"]
        allowed = extract_numbers_with_paths(bundle)

        print(f"\n{cid}: plan run")
        try:
            check_plan_response(cid, make_plan(cid), allowed)
        except Exception as e:
            check(False, f"{cid}: plan run raised {type(e).__name__}: {e}")

        for pid in PLANS:
            print(f"\n{cid}: challenge plan {pid}")
            try:
                check_challenge(cid, pid, make_challenge(cid, pid), allowed)
            except Exception as e:
                check(False, f"{cid} plan {pid}: raised "
                             f"{type(e).__name__}: {e}")

    print(f"\n{'=' * 60}")
    if failures:
        print(f"{len(failures)} failures:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    print("every customer, every plan, all clean")


if __name__ == "__main__":
    main()
