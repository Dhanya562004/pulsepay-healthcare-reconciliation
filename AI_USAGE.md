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
