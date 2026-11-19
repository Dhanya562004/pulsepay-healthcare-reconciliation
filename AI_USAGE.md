# AI Usage Log

## Phase 0: Cleanup & Baseline Verification

### Agent
- Model: Gemini 3.8 Flash (High)

### Actions Taken
1. Checked repository code, routes, CORS configuration, database configuration, and test files.
2. Verified endpoints, absence of `GET /payments` and `GET /payments/{id}`, pagination support on `GET /invoices`, and lack of authentication.
3. Cleaned `README.md`: removed unverified claims and hype words ("Production-Grade", "Sub-50ms", "Real-World Healthcare Financial Infrastructure"), described the project plainly as a billing, payments, and reconciliation simulation, and added a "Known Limits" section.
4. Updated `.env.example` to ensure every environment variable is listed with clear placeholder values and no real secrets.

### Mistakes & Corrections Log
1. Attempted running `gh --version` to check for GitHub CLI availability. The command failed because `gh` is not installed on the system path.
   - *Correction / Fallback*: Provided the branch push and PR title/description manually for the user as instructed.
2. Verified existing tests by executing `pytest` in terminal. Exit code was 1 (`collected 0 items; no tests ran in 0.03s`).
   - *Confirmation*: Confirmed that no pytest suite exists, only `scripts/simulate_webhooks.py`.

---

## Phase 1: Backend API Enhancement, Authentication, CORS & Tests

### Agent
- Model: Gemini 3.8 Flash (High)

### Actions Taken
1. Added paginated `GET /payments` endpoint with `limit` (1-100 validated, HTTP 422 on bad values), `offset`, optional `status` filter, and response shape `{ "data": [...], "pagination": { "limit": n, "offset": n, "total": n, "hasMore": bool } }`.
2. Added `GET /payments/{id}` returning full payment detail (including invoice id, status, provider, amount, timestamps, and related webhook event statuses), returning clean HTTP 404 with JSON error for unknown IDs.
3. Configured CORS in `backend/main.py` using `CORS_ALLOWED_ORIGINS` (comma-separated), disallowing `*` with credentials, and defaulting to blocking cross-origin access when unset.
4. Implemented constant-time `X-Api-Key` authentication middleware enforcing HTTP 401 for missing key and HTTP 403 for invalid key across all endpoints except `GET /` and `/docs`, `/redoc`, `/openapi.json`. Added startup validation failing startup with `RuntimeError` if `API_KEY` is unset in `ENVIRONMENT=production`.
5. Updated `app.py` and `scripts/simulate_webhooks.py` to send `X-Api-Key` header from environment / Streamlit secrets, and updated payment retrieval to use the new paginated endpoint.
6. Created isolated pytest test suite (`tests/test_auth.py`, `tests/test_cors.py`, `tests/test_payments.py`, `tests/test_webhooks.py`) using in-memory SQLite and verified 16 passing tests.

### Mistakes & Corrections Log
1. In `tests/test_webhooks.py`, the initial test assertion looked for `"DUPLICATE_IGNORED"` in `detail["webhook_event_statuses"]`. However, checking `backend/services/webhook_service.py` confirmed that incoming duplicate webhooks with identical `event_id` are caught early by the idempotency guard and rejected with `{"status": "ignored"}` without creating a second row in `webhook_events` (since `event_id` is unique in SQLite/PostgreSQL).
   - *Correction*: Updated `test_webhooks.py` to assert that the duplicate webhook request returns `status="ignored"` with the idempotency message, and that the payment detail accurately reflects the original processed webhook event.

---

## Phase 2: Next.js Frontend Application (`web/`)

### Agent
- Model: Gemini 3.8 Flash (High)

### Actions Taken
1. Initialized Next.js 14 App Router application with TypeScript strict mode enabled in `web/`.
2. Built server-only API client (`web/lib/api.ts`) utilizing `PULSEPAY_API_URL` and `PULSEPAY_API_KEY` without exposing keys to the browser, with ISR fetch revalidation (30s) on the list and dynamic `cache: 'no-store'` on the detail page.
3. Implemented `/payments` with server-rendered paginated table driven by URL `searchParams` (`?page=...&status=...`), Zod validation and safe fallbacks, status filtering, accessible keyboard pagination, `loading.tsx`, `error.tsx`, and empty state.
4. Implemented `/payments/[id]` detail page with full transaction metadata, webhook event timeline, and `notFound()` handling with `not-found.tsx`.
5. Created `web/lib/format.ts` for consistent currency and timestamp formatting.
6. Added lazy loading with `next/dynamic` for `StatusBreakdownChart` with loading fallback.
7. Configured strict security headers (CSP, X-Content-Type-Options, X-Frame-Options, Referrer-Policy) in `next.config.mjs`.
8. Added Vitest unit test suite (17 tests) covering formatters and search parameter validation.
9. Verified lint, type-check, unit tests, and production build with real bundle sizes.

### Mistakes & Corrections Log
1. The repository root `.gitignore` contained a bare `lib/` pattern originally intended for Python virtual environment folders. This caused Git to ignore `web/lib/`.
   - *Correction*: Added `!lib/` and `!lib/**` to `web/.gitignore` to properly track `web/lib/format.ts`, `web/lib/search-params.ts`, and `web/lib/api.ts` without needing to modify root Python ignore patterns.
2. An attempt to upgrade Next.js to `^14.2.25` encountered Windows file-lock contention and a transient network ECONNRESET. Next.js 14.2.15 was retained, verified cleanly passing type-check, lint, tests, and production build.

---

## Phase 3: Playwright End-to-End Testing

### Agent
- Model: Gemini 3.8 Flash (High)

### Actions Taken
1. Added Playwright (`@playwright/test` and Chromium) to `web/` with single-worker, deterministic, zero-retry configuration in `web/playwright.config.ts`.
2. Created test backend runner (`web/scripts/start_test_backend.py`) that boots FastAPI on `127.0.0.1:8000` with an isolated temporary SQLite database, a test-only API key (`test-playwright-secret-key-xyz`), and deterministic mock data (15 payments, multi-event webhook timeline, and an XSS probe record).
3. Configured Playwright's dual `webServer` orchestration to run both the FastAPI test backend and the Next.js production build (`npm run start -- -p 3000`) locally, ensuring complete isolation from production and live Render deployments.
4. Implemented full E2E test suite in `web/e2e/payments.spec.ts` covering:
   - Payment list table rows (10 rows on page 1) and pagination controls.
   - Next page navigation (`?page=2`), URL transition, and updated page rows.
   - Status filtering narrowing table rows to matching status.
   - Payment detail view with full metadata and 3-event webhook timeline.
   - Unknown payment ID rendering HTTP 404 not-found page with return link.
   - XSS sanitization verifying `<script>alert(1)</script>` renders as plain text without script execution or dialog triggers.
   - Secret key isolation asserting that the backend `API_KEY` never appears in page HTML source or browser-initiated network requests.
5. Created `web/README.md` documenting setup, scripts, dual-server testing architecture, and Playwright execution commands.

### Mistakes & Corrections Log
1. In PowerShell, running `curl -H ...` threw a parameter binding error because `curl` is an alias for `Invoke-WebRequest` in Windows PowerShell.
   - *Correction*: Invoked `curl.exe` directly to verify local backend HTTP responses.
2. During the initial `npx playwright install chromium` execution, a transient network TLS reset (`ECONNRESET`) occurred when downloading browser packages from `cdn.playwright.dev`. Playwright's built-in retry logic caught the error and completed the download cleanly on retry.
3. In `web/e2e/payments.spec.ts`, Playwright strict mode locators `getByText('stripe')` and `getByText('PROCESSED')` matched multiple elements because substring matching caught transaction reference `tx_stripe_detail_001` and event ID `evt_processed_001`.
   - *Correction*: Specified `{ exact: true }` so locators strictly target the intended badge spans.
4. Comparing the first table cell text on page 1 vs page 2 compared `"pay-seq-..."` on both pages due to UI ID slicing (`.slice(0, 8)`).
   - *Correction*: Compared the unique link `href` attribute (`/payments/${id}`) to assert row transition between pagination pages.
5. `npm run test` (Vitest) attempted to execute Playwright test file `web/e2e/payments.spec.ts` because default Vitest matchers include `**/*.spec.ts`.
   - *Correction*: Added `exclude: [...configDefaults.exclude, "e2e/**"]` in `web/vitest.config.ts`.

---

## Phase 4: CI/CD Automation, Documentation & Deployment Readiness

### Agent
- Model: Gemini 3.8 Flash (High)

### Actions Taken
1. Created `.github/workflows/ci.yml` defining continuous integration jobs: `backend-pytest`, `web-lint`, `web-type-check`, `web-unit-tests`, `web-build`, and `playwright-e2e`. Configured dependency caching (pip, npm, Playwright browser cache), test-only environment keys, and full local runner isolation (never contacting live Render services).
2. Rewrote `web/README.md` in plain words detailing the application purpose, required server-side environment variables (`PULSEPAY_API_URL`, `PULSEPAY_API_KEY`), setup/run instructions, testing commands, and known limitations.
3. Added a dedicated "Web App (Next.js)" section to the root `README.md` including a feature overview, table link, and screenshot placeholder.
4. Compiled explicit manual deployment checklist for Vercel and Render CORS configuration.
5. Executed and verified all quality and test suites locally: lint, type-check, unit tests, Next.js build, Playwright E2E, and backend pytest.

### Mistakes & Corrections Log
1. Attempted running recursive search for `.github` across the repository with PowerShell without excluding `node_modules`, generating an excessively verbose path listing through transitive dependency folders.
   - *Correction*: Targeted the root directory specifically using `Test-Path .github`.



