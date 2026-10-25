# Status

Phases 1 through 5 of the pilot are complete:

- `backend/`: FastAPI and SQLite API for the 25-claim queue, full claim detail, ordered activity, decisions, handler sign-off and simulated payment
- `agent/`: LangChain `create_agent` entry point with structured decisions, backend-only tools and a deterministic test mode
- `dashboard/`: branded React handler workspace with the queue, full claim evidence, decisions, live activity, read-only instructions, sign-off and payment controls
- `e2e/`: six isolated Playwright journeys for dashboard loading, approve, decline, refer, high-value sign-off and payment, persistence, privacy, responsive layout and browser errors
- root commands: `npm run dev`, `npm run check:python`, `npm run check:ts` and `npm run check:e2e`

The seed process reads the operational JSON and policy wording only. It does not read evaluation data, the security fixture or the claims manual.

The backend owns the workflow guardrails. Approvals over $1,000 wait for a valid handler sign-off, declined and referred claims cannot be paid, and payment must match the approved payout.

The agent receives an allowlisted decision context. Customer and traveler names, customer ID, email, phone, address and date of birth are excluded; known occurrences are redacted from claim and document text before the model call. The model has no full-claim, filesystem, evaluation-data or claims-manual tool.

Set `UNDERCOVER_STUB_AGENT=1` to exercise agent flows without a model request. Production uses `MODEL_NAME` when set and otherwise `openai/gpt-6-luna` through OpenRouter.

Run `uv sync` and `npm install`, then `npm run dev`. The API is at `http://127.0.0.1:8000` and the dashboard is at `http://127.0.0.1:5173`.

The remaining work is the final clean dependency and full quality-gate verification.
