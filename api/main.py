"""
The API. Three endpoints from contract section 12, and nothing else.

This file joins nothing and calculates nothing - it takes a request, calls the
pipeline, returns the result. All the real work is in orchestrator/pipeline.py.

Run:  uvicorn api.main:app --reload
Docs: http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from orchestrator.pipeline import engine_status, make_challenge, make_plan

app = FastAPI(title="Finance Planner", version="api-v1")

# The React app runs on a different port, so without this the browser blocks
# every call. Open during the hackathon; a real deployment would list origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, ValueError):
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc)},
        )
    # Do not leak internal stack traces
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

def check_verifier(res: dict):
    if res.get("verifier", {}).get("status") == "fail":
        raise ValueError("Explanation failed verification")
    return res


class PlanRequest(BaseModel):
    customer_id: str


class ChallengeRequest(BaseModel):
    customer_id: str
    chosen_plan_id: str


class WhatIfRequest(BaseModel):
    customer_id: str
    extra_monthly_savings: int


@app.post("/api/plan")
def plan(request: PlanRequest):
    """The main call. Returns section 11 - profile, risk, three plans, prose."""
    return check_verifier(make_plan(request.customer_id))


@app.post("/api/challenge")
def challenge(request: ChallengeRequest):
    """Runs only after the customer picks a plan. Returns section 10."""
    return check_verifier(make_challenge(request.customer_id, request.chosen_plan_id))


@app.post("/api/whatif")
def whatif(request: WhatIfRequest):
    """Same as /api/plan with a bigger monthly surplus.

    Wired end to end, but do not demo it until the plan generator is real: right
    now the surplus in the response goes up and the plan numbers do not move,
    because the mock returns fixed plans whatever you feed it.
    """
    return check_verifier(make_plan(request.customer_id, request.extra_monthly_savings))


@app.get("/api/status")
def status():
    """Which stages are real engines and which are still mocks.

    Here so nobody has to ask in the group chat, and so the demo can say out
    loud which numbers are computed rather than being asked and guessing.
    """
    stages = engine_status()
    return {
        "stages": stages,
        "engines_live": sum(v == "engine" for v in stages.values()),
        "stages_total": len(stages),
    }
