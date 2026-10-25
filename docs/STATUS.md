# Status

Phase 1 of the pilot is complete:

- `backend/`: FastAPI health route and idempotent SQLite bootstrap for the 25 operational claims and their related records
- `agent/`: the typed `run(claim_id, thread_id)` entry point ready for the claim workflow
- `dashboard/`: React, Vite and Vitest application foundation
- `e2e/`: Playwright application smoke test
- root commands: `npm run dev`, `npm run check:python`, `npm run check:ts` and `npm run check:e2e`

The seed process reads the operational JSON and policy wording only. It does not read evaluation data, the security fixture or the claims manual.

Run `uv sync` and `npm install`, then `npm run dev`. The API is at `http://127.0.0.1:8000` and the dashboard is at `http://127.0.0.1:5173`.

The claims workflow, privacy-safe agent, operational dashboard and full end-to-end journeys are still to be built in the remaining phases.
