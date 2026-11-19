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
