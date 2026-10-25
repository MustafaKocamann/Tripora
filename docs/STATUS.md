# Status

Phases 1 and 2 of the pilot are complete:

- `backend/`: FastAPI and SQLite API for the 25-claim queue, full claim detail, ordered activity, decisions, handler sign-off and simulated payment
- `agent/`: the typed `run(claim_id, thread_id)` entry point ready for the claim workflow
- `dashboard/`: React, Vite and Vitest application foundation
- `e2e/`: Playwright application smoke test
- root commands: `npm run dev`, `npm run check:python`, `npm run check:ts` and `npm run check:e2e`

The seed process reads the operational JSON and policy wording only. It does not read evaluation data, the security fixture or the claims manual.

The backend owns the workflow guardrails. Approvals over $1,000 wait for a valid handler sign-off, declined and referred claims cannot be paid, and payment must match the approved payout.

Run `uv sync` and `npm install`, then `npm run dev`. The API is at `http://127.0.0.1:8000` and the dashboard is at `http://127.0.0.1:5173`.

The privacy-safe agent, operational dashboard and full end-to-end journeys are still to be built in the remaining phases.
