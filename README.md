# Finance Planner

GenAI financial planning system. Generates 2-3 personalised plans from a
customer's net worth, goals and transaction history.

## Setup
pip install -r requirements.txt

## Structure
docs/      - JSON_CONTRACT.md, the frozen data contract. Read it first.
engines/   - compute layer. All numbers are produced here.
agents/    - GenAI layer. Language only, never numbers.
mocks/     - fake JSON so every module can be built independently.
frontend/  - UI
tests/     - pytest

## Rules
- Never push to main. Branch, then pull request.
- Do not change a contract field without telling the group.