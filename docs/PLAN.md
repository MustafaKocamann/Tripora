# Pilot implementation plan

## Approach

Build the pilot in six phases, with the backend as the system of record and the enforcement boundary. The dashboard may display the full claim record to handlers, but the agent receives a separate, minimal decision context. The agent never reads files directly: it uses only its dedicated backend tools, and those tools do not expose evaluation data, the claims manual or unnecessary personal data.

The pilot covers only the current brief: the claims queue, claim details, live agent activity, read-only agent instructions, decisions, payout calculation and handler sign-off above $1,000. It does not add sign-in, customer messaging, real payments, the claims manual or later-course architecture.

## Model data boundary

The decision model will receive an allowlisted context assembled by the backend rather than a serialized customer, claim or policy database object.

Allowed decision data:

- the opaque claim ID, claim type, submitted and incident dates, incident location, summary, story, claimed items, amount and supporting-document text
- the plan, add-ons, coverage limits, deductibles, trip facts and policy status needed to apply the policy
- prior-claim facts needed by the brief: dates, claim types, summaries, outcomes and amounts, without customer contact or demographic fields
- the policy wording and the agent instructions

The model must not receive the customer's name, customer ID, email address, phone number, postal address, date of birth, traveler names or the complete customer record. Known occurrences of those values will also be redacted from free-text fields before a tool response enters the model context. The generic handler-facing claim endpoint will not be available as an agent tool. Model requests and activity logs will not store the excluded values.

This boundary will be tested by capturing the exact messages and tool responses passed to a stub model and asserting both that required decision facts are present and that the forbidden field names and source values are absent.

## Phase 1: Application foundation and seeded data

Create the FastAPI, agent, React/Vite and test application structure expected by the existing root commands. Add typed domain models and an idempotent SQLite bootstrap that imports the operational files in `data/` while explicitly excluding `data/evals/`, `data/security/` and `claims_manual.md`. Keep source records intact in the backend so handlers can inspect full claims, while preparing separate response models for later privacy enforcement.

Why: every later feature needs one predictable data model, repeatable local startup and a firm separation between operational records and prohibited evaluation material.

Success criteria:

- [x] `uv run pytest backend/tests/test_seed.py -q` passes and proves a fresh database contains the 25 queue claims and their related policies, customers, plans and company settings.
- [x] Running the bootstrap twice produces the same record counts and does not duplicate claims, documents, items or history.
- [x] A test spies on every seed file opened and proves nothing under `data/evals/` or `data/security/`, and no claims-manual file, is read.
- [x] `uv run ruff format --check backend agent` and `uv run ruff check backend agent` pass.
- [x] `uv run pyright backend agent` reports zero errors.
- [x] `GET /api/health` returns HTTP 200 and exactly `{"status":"ok"}` after `uv run -m uvicorn backend.main:app --port 8000` starts.
- [x] `npm run dev` starts the backend on port 8000 and the dashboard on port 5173 from one PowerShell command.

## Phase 2: Claims API and enforced workflow

Implement the queue, full claim detail, decision, activity, sign-off and simulated-payment operations. Use explicit states for waiting, in progress, waiting for sign-off and decided. Keep recording a decision separate from paying a claim. Enforce the company approval threshold in backend domain code so no caller, including the agent, can pay more than $1,000 before a handler signs off.

Every API operation will have a unique `operation_id`, a one-line docstring and required inputs only. State changes will create ordered activity records so the dashboard can show what happened without reconstructing it from logs.

Why: business safeguards belong in deterministic server code, not in prompts or frontend controls.

Success criteria:

- [x] `uv run pytest backend/tests/test_claims_api.py backend/tests/test_workflow.py -q` passes for queue listing, claim detail, all three decisions, activity ordering, sign-off and payment.
- [x] `GET /api/claims` returns HTTP 200 with all 25 claims and their queue states; it contains no held-out or security claim.
- [x] `GET /api/claims/{claim_id}` returns the complete handler-facing claim, policy, customer history, documents, decision, activity and payment state.
- [x] Recording an approval of $1,000 or less can reach `decided`; recording an approval over $1,000 reaches `waiting_for_sign_off`.
- [x] Before sign-off, `POST /api/claims/{claim_id}/payments` with `{"amount":1250.0}` returns HTTP 409 with `{"detail":"Handler sign-off required"}` and creates no payment.
- [x] After a required-handler sign-off operation, the separate payment operation accepts the approved amount and records a simulated payment; an incorrect amount is rejected.
- [x] Declined and referred claims cannot be paid, regardless of caller or amount.
- [x] `/openapi.json` tests prove every operation has a unique explicit operation ID, a one-line summary/docstring and no optional request inputs.

## Phase 3: Privacy-safe UnderCover Agent

Implement `agent.run(claim_id, thread_id)` with LangChain `create_agent`. Use the model in `MODEL_NAME` when set, otherwise `openai/gpt-6-luna` through OpenRouter with low reasoning effort. Give the agent narrowly scoped tools for the privacy-safe decision context, policy wording, activity updates, decision recording and payment attempts. Serve the read-only instructions through the backend and require a structured approve, decline or refer result with payout and a two- or three-sentence rationale naming the relevant policy section.

Build the decision-context mapper as an explicit allowlist. It will derive needed coverage and history facts without passing customer or traveler identity fields, and it will redact the known excluded values if they occur in story or document text. The agent will have no arbitrary HTTP or filesystem tool and no handler-facing full-record tool.

Why: the model needs enough evidence to decide the claim, but contact, identity and demographic data are neither necessary nor appropriate for that decision.

Success criteria:

- [x] `uv run pytest agent/tests -q` passes using only stub models; no test makes a real model request.
- [x] Stub scenarios prove approve, decline and refer results are persisted with the correct payout, two- or three-sentence rationale and relevant policy section.
- [x] `run(claim_id, thread_id)` marks a claim in progress, records ordered activity, records one final decision and returns the stored result.
- [x] A captured model call contains the required claim, coverage, history and policy facts but contains none of these keys: `name`, `customer_id`, `email`, `phone`, `address`, `date_of_birth` or traveler identity fields.
- [x] The same captured call contains none of the corresponding source values, even when a known email, phone number, address, birth date or name is repeated inside story or document text.
- [x] Tests prove the agent tools cannot fetch the generic full claim endpoint, `data/evals/`, `data/security/` or `claims_manual.md`.
- [x] An approval over $1,000 can be recorded, but the agent's attempted payment is rejected by the backend and leaves the claim waiting for sign-off.
- [x] An invalid model result is not silently accepted and leaves a clear failed activity event without creating a decision or payment.

## Phase 4: Handler dashboard

Build the React dashboard with a queue overview, full claim detail, ordered live activity and read-only agent-instructions view. Poll the backend while a claim is in progress so handlers can follow the agent step by step. Add controls to run a waiting claim, sign off an eligible high-value approval and record its simulated payment.

Apply the UnderCover brand with Instrument Sans, Instrument Serif and JetBrains Mono; the specified light/dark surfaces and semantic colors; rounded borderless panels; short US-English labels; and US-dollar formatting. Keep TypeScript strict with no `any`.

Why: handlers need one clear operational view of the queue, evidence, reasoning and safeguards rather than a developer console.

Success criteria:

- [ ] `npm run check:ts` passes ESLint, Prettier, TypeScript and Vitest with at least 80% frontend coverage.
- [ ] Component tests cover loading, empty and error states; all four queue states; claim evidence; decision and payout display; activity ordering; and read-only instructions.
- [ ] Component tests prove sign-off and payment controls appear only in valid states and use separate API operations.
- [ ] In the browser, `/` shows all 25 queue claims with waiting, in-progress, waiting-for-sign-off or decided status, with money formatted like `$1,250.00`.
- [ ] In the browser, selecting a claim shows its story, items, documents, policy, customer history, decision and reasons without exposing any evaluation answer.
- [ ] In the browser, starting a claim visibly changes its state and appends activity in order until the stubbed decision appears.
- [ ] In the browser, the instructions page is readable but has no edit control.
- [ ] Playwright MCP inspection at desktop and narrow viewport sizes confirms the brand, usable layout, keyboard focus, accessible names and no browser-console errors.

## Phase 5: End-to-end journeys

Add deterministic Playwright journeys backed by a stub agent so the complete application is tested without model spend. Cover the ordinary decision paths and the high-value approval safeguard through the same HTTP and UI boundaries used in production.

Why: unit tests prove the pieces, while these journeys prove the backend, dashboard, persistence and guardrails work together.

Success criteria:

- [ ] `npm run check:e2e` starts its own backend and dashboard and all Playwright tests pass without a real model key.
- [ ] An approval journey moves a waiting claim through in-progress to decided and displays its payout and policy-based rationale.
- [ ] Decline and refer journeys display a zero payout and the stored reasons.
- [ ] A high-value approval journey reaches waiting for sign-off, proves payment is blocked, records handler sign-off, then records the separate simulated payment.
- [ ] Refreshing a decided or waiting-for-sign-off claim preserves its state, decision and activity from SQLite.
- [ ] A browser-network assertion proves agent execution calls only the dedicated run operation; a backend spy again proves the model payload contains no forbidden personal fields or values.
- [ ] Queue, claim, activity and instructions pages have no uncaught browser errors and no failed API requests in their expected flows.

## Phase 6: Final verification and handover

Run the complete quality gate, verify clean startup on Windows and update the project status with the implemented architecture, commands and known pilot limits. Check the final application against every requirement in `docs/SPEC.md` and this plan, then commit the phase only after the pre-commit hook passes.

Why: the pilot is complete only when a fresh checkout can install, start and verify the same behavior reproducibly.

Success criteria:

- [ ] From a clean dependency state, `uv sync` and `npm install` complete successfully and install the Lefthook pre-commit hook.
- [ ] `npm run dev` starts both services; `/api/health` returns HTTP 200 and `http://localhost:5173` loads the queue.
- [ ] `npm run check` passes Ruff format/lint, pyright, pytest with at least 80% coverage, ESLint, Prettier, TypeScript, Vitest with at least 80% coverage and all Playwright tests.
- [ ] A final Playwright MCP walkthrough verifies the queue, full claim, live activity, instructions, approve, decline, refer, sign-off and payment-blocking behavior.
- [ ] A final privacy test report names every forbidden field and confirms that neither its key nor its source value reached the captured model request.
- [ ] `docs/STATUS.md` accurately describes what is built, how to run it, the privacy boundary and the pilot's excluded features.
- [ ] Each phase has its completed criteria ticked here and its own verified commit; no commit bypasses Lefthook and nothing is pushed.
