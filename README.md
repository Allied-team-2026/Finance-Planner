# Finance Planner

A GenAI financial planner. Give it a customer and it returns three personalised
investment plans, each with a plain-English explanation, a Monte Carlo success
probability, a stress test, a peer comparison, and — once the customer picks one
— an argument against that choice.

Banking domain, problem statement 9. Three demo customers: C001 Rahul Mehta,
C002 Vihaan Sharma, C003 Vivaan Patel.

## The one rule

**Engines calculate. Agents talk. The UI only reads.**

No agent and no React component may produce, compute, round, convert or guess a
number. Every number on screen was computed by an engine in `engines/`, carried
through the bundle, and printed as-is. Two consequences worth knowing before you
change anything:

- **A dash, never a guess.** If a number is missing, the UI shows `—` in neutral
  grey. It never falls back to a plausible default. `|| 45000` is the bug, not
  the fix.
- **No PII reaches the LLM.** No name, no `customer_id`, no transactions. The
  agent payload is built in `build_bundle` (`orchestrator/pipeline.py`), which is
  the single place identifiers are dropped. The name is re-attached afterwards.

The agents check their own output against the engines' numbers and refuse to
answer rather than invent one. `agents/verifier.py` then checks them again.

## Run it

One-time setup:

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

Create a `.env` in the repo root with your own Groq key. `.env` is gitignored,
this repo is public, and a committed key cannot be quietly undone — it stays in
git history and has to be revoked for everyone. Generate your own at
console.groq.com; do not share one.

```
GROQ_API_KEY=your_key_here
```

Then two terminals, both from the repo root:

```
# terminal 1 - backend
source venv/bin/activate
uvicorn api.main:app --reload

# terminal 2 - frontend
cd frontend
npm run dev
```

Open the URL Vite prints, normally <http://localhost:5173>.

Do not open port 8000 in a browser expecting the app — that is the API, and `/`
there is a 404 by design. Swagger is at <http://localhost:8000/docs>.

First thing to check after starting: <http://localhost:8000/api/status> should
report 11 of 11 stages live and `"challenge": "engine"`. If any stage says
`mock`, that stage is returning C001's canned fixture regardless of who you
asked about, so the screen will show one customer's money under another
customer's name.

Two things that look like faults and are not. The first plan request is slow,
because the risk model trains on first use and the peer cohort dataset is built
per request. And if uvicorn says the port is busy, clear it with
`lsof -ti:8000 | xargs kill`.

## API

| Endpoint | What it does |
| --- | --- |
| `POST /api/plan` | The main call. Three plans plus all the prose. |
| `POST /api/challenge` | The argument against a chosen plan. Runs after the customer picks one. |
| `POST /api/whatif` | `/api/plan` again with a larger monthly surplus. |
| `GET /api/status` | Which stages are real engines and which are mocks. |
| `GET /api/customer/{id}` | Demographics and profile only. No LLM, so it is fast. |

## Test it

```
python -m pytest -q          # the whole suite, offline except one live test
python tools/live_matrix.py  # all 3 customers x 3 plans against the real LLM
python tools/verify_mocks.py # mocks still match the contract
```

If bare `pytest` fails with `ModuleNotFoundError: No module named 'orchestrator'`,
use `python -m pytest` instead — the console script does not always put the repo
root on the import path.

`live_matrix.py` spends real Groq tokens on purpose. The bug it exists to catch
was one customer's numbers appearing on another customer's screen, and that only
shows up when the model is really writing the text. Run it before demo day and
after any change to an agent prompt. It exits non-zero if anything is wrong.

If a live test fails with a 429, that is the daily token limit, not a code bug.
Swap in another key.

## Structure

```
docs/JSON_CONTRACT.md  the frozen data contract. Read it first.
engines/               compute layer. Every number is produced here.
models/                the revealed-risk model. Trains in-process on first use.
agents/                GenAI layer. Language only, never numbers.
orchestrator/          wiring. build_bundle drops PII; nothing here computes.
api/                   FastAPI. Thin - it calls the orchestrator and returns.
frontend/              React and Vite. Reads and paints, decides nothing.
mocks/                 fixtures, so any module can be built independently.
tools/                 live_matrix.py and verify_mocks.py.
tests/                 pytest.
```

Any stage can be swapped between its real engine and its mock with a one-line
change: `PRODUCTION_ENGINES` in `orchestrator/pipeline.py`. Mocks ignore their
arguments, which is the point — and also why a mocked stage always answers as
C001.

## Team rules

- Never push to `main`. Branch, then pull request. Only Shlok merges.
- Do not change a contract field without telling the group.
- `docs/JSON_CONTRACT.md`, `requirements.txt`, `README.md` and `.gitignore` are
  add-only. Nobody edits `requirements.txt` directly.
- Nobody creates or overwrites anything in `mocks/`.
- Never commit a key, a `.env`, or real customer data.
