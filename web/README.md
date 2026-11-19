# PulsePay Web Frontend

A Next.js (App Router, TypeScript strict mode) web application providing an operator interface for the PulsePay healthcare payment reconciliation simulation.

---

## What It Is

The PulsePay Web Frontend is a server-rendered operator portal that displays payment records and financial reconciliation events. It provides:
- A paginated list of payment transactions with status filtering.
- A dedicated payment detail view showing transaction metadata and an audit timeline of received webhook events (`PROCESSED`, `DUPLICATE_IGNORED`, `DELAYED_IGNORED`).
- Complete API secret isolation: the browser client never receives or sees the backend `API_KEY`. All backend communication occurs strictly on the server through Next.js server components and route handlers.

---

## Environment Variables

The web application requires two environment variables configured on the server side (documented in `.env.example`):

| Variable | Description | Example (Local) |
| :--- | :--- | :--- |
| `PULSEPAY_API_URL` | Base URL of the FastAPI backend service | `http://127.0.0.1:8000` |
| `PULSEPAY_API_KEY` | Secret API key passed in `X-Api-Key` for backend authentication | `your-secret-api-key` |

> **Security Note**: Neither variable is prefixed with `NEXT_PUBLIC_`. They are never embedded in client bundles or transmitted to the browser.

To set up locally:
```bash
cp .env.example .env.local
```
Then edit `.env.local` with your local or staging backend configuration.

---

## How to Run

### 1. Prerequisites
- Node.js 18.x or higher
- npm 9.x or higher
- Python 3.10+ (if running the local FastAPI test backend or Playwright suite)

### 2. Install Dependencies
```bash
npm install
```

### 3. Development Server
Starts the Next.js development server on `http://localhost:3000`:
```bash
npm run dev
```

### 4. Production Build & Start
Creates an optimized production bundle and starts the production server on `http://localhost:3000`:
```bash
npm run build
npm run start
```

---

## How to Test

### Code Quality & Unit Tests
- **Lint**: Run ESLint to check code style and Next.js best practices:
  ```bash
  npm run lint
  ```
- **Type Check**: Run the TypeScript compiler with no emit to verify types:
  ```bash
  npm run type-check
  ```
- **Unit Tests**: Run Vitest to test formatting utilities (`lib/format.ts`) and query parameter validation (`lib/search-params.ts`):
  ```bash
  npm run test
  ```

### End-to-End Tests (Playwright)
The Playwright test suite executes against an isolated local environment—it never connects to live or remote backends.

1. **Run full E2E suite**:
   ```bash
   npm run test:e2e
   ```
   *(Or run directly via Playwright: `npx playwright test`)*

2. **How test orchestration works**:
   - Playwright's configuration (`playwright.config.ts`) automatically launches two local servers before running tests:
     - **Local FastAPI test backend** (`scripts/start_test_backend.py` on `127.0.0.1:8000`) using an isolated temporary SQLite database seeded with deterministic test data.
     - **Next.js production server** on `127.0.0.1:3000`.
   - The suite verifies list rendering, pagination transitions (`?page=2`), status filtering, detail page metadata, webhook timeline statuses, 404 handling, plain-text XSS sanitization, and API key isolation.
   - Servers are terminated cleanly when tests finish.

---

## Known Limits

- **Read-Only Interface**: The web app displays payment data and reconciliation event timelines. Initiating payments or triggering simulated webhook deliveries is handled via the backend API or the Streamlit simulator.
- **Backend Availability Dependency**: If the FastAPI backend is down or unreachable, Next.js server components render graceful error boundary fallbacks with retry options.
- **No Real-Time WebSockets**: Data is fetched on request and refreshed through page transitions or revalidation intervals (30-second ISR on payments list; dynamic no-store on detail page), rather than persistent WebSocket connections.
- **Single Currency & Fixed Formatting**: Monetary values are formatted as US Dollars ($ USD) using standard locale formatters.
- **Free-Tier Cloud Cold Starts**: When deployed against a free-tier hosted backend (such as Render), the initial server-side fetch after inactivity may take 50+ seconds while the backend resumes from sleep.
