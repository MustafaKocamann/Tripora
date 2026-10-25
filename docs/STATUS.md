# Status

The six-phase pilot is complete:

- `backend/`: FastAPI and SQLite API for the 25-claim queue, full claim detail, ordered activity, decisions, handler sign-off and simulated payment
- `agent/`: LangChain `create_agent` entry point with structured decisions, backend-only tools and a deterministic test mode
- `dashboard/`: branded React handler workspace with the queue, full claim evidence, decisions, live activity, read-only instructions, sign-off and payment controls
- `e2e/`: six isolated Playwright journeys for dashboard loading, approve, decline, refer, high-value sign-off and payment, persistence, privacy, responsive layout and browser errors
- root commands: `npm run dev`, `npm run check`, `npm run check:python`, `npm run check:ts` and `npm run check:e2e`

The seed process reads the operational JSON and policy wording only. It does not read evaluation data, the security fixture or the claims manual.

The backend owns the workflow guardrails. Approvals over $1,000 wait for a valid handler sign-off, declined and referred claims cannot be paid, and payment must match the approved payout.

The agent receives an allowlisted decision context. Customer and traveler names, customer ID, email, phone, address and date of birth are excluded; known occurrences are redacted from claim and document text before the model call. The model has no full-claim, filesystem, evaluation-data or claims-manual tool.

Set `UNDERCOVER_STUB_AGENT=1` to exercise agent flows without a model request. Production uses `MODEL_NAME` when set and otherwise `openai/gpt-6-luna` through OpenRouter.

Run `uv sync` and `npm install`, then `npm run dev`. The API is at `http://127.0.0.1:8000` and the dashboard is at `http://127.0.0.1:5173`.

Run `uv run lefthook install` once after a fresh checkout to install the pre-commit hook. `npm run check` is the complete local quality gate.

## Final verification

Verified on October 25, 2026:

- `uv sync` and `npm install` completed successfully; Lefthook 2.2.2 installed the pre-commit hook.
- `npm run dev` returned `{"status":"ok"}` from the API and HTTP 200 from the dashboard.
- `npm run check` passed 19 Python tests at 93.11% coverage, 19 frontend tests at 95.6% line and 85% branch coverage, and six Playwright journeys.
- The privacy tests captured the decision context/model input and rejected the keys and source values for `name`, `customer_id`, `email`, `phone`, `address`, `date_of_birth` and `travelers`. Names or other known personal values repeated in free text were replaced by `[REDACTED]`.

The pilot deliberately excludes the claims manual, sign-in, real payments, customer messages and later-course production architecture. Simulated payments stay behind backend workflow guards.
