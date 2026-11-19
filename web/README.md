# PulsePay Web Frontend

A Next.js (App Router, TypeScript strict mode) web application for the PulsePay healthcare payment reconciliation simulation.

## Overview

The web client provides healthcare operators with a paginated overview of payments and an event-by-event reconciliation timeline for individual transactions.

### Key Architecture & Security Guardrails
- **API Secret Isolation**: The browser client NEVER receives or sees the backend `API_KEY`. All communication with FastAPI occurs strictly through Next.js server components using `PULSEPAY_API_URL` and `PULSEPAY_API_KEY`.
- **Search Parameter Validation**: Pagination (`page`) and status filters (`status`) are validated with Zod, gracefully falling back to safe defaults on malformed inputs.
- **Strict Content Security Policy**: Configured in `next.config.mjs` with `script-src 'self'`, `object-src 'none'`, and standard security headers (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`).
- **Safe Rendering**: All dynamic API data is rendered as plain text (no `dangerouslySetInnerHTML`).

---

## Getting Started

### Prerequisites
- Node.js 18.x or higher
- Python 3.10+ (with repository root backend dependencies installed for test runs)

### Environment Setup
Copy the example environment configuration:
```bash
cp .env.example .env.local
```
Configure your local environment variables in `.env.local`:
- `PULSEPAY_API_URL`: Base URL of the FastAPI backend (e.g., `http://127.0.0.1:8000`)
- `PULSEPAY_API_KEY`: Secret API key for authenticating server-to-server requests with FastAPI

---

## Available Scripts

### Development Server
Runs the Next.js development server on `http://localhost:3000`:
```bash
npm run dev
```

### Production Build & Run
```bash
npm run build
npm run start
```

### Code Quality & Unit Tests
- **Lint**: `npm run lint`
- **Type Check**: `npm run type-check`
- **Unit Tests (Vitest)**: `npm run test`

---

## End-to-End Testing (Playwright)

End-to-end tests are written with Playwright to verify core user journeys, pagination, status filtering, webhook timelines, 404 handling, XSS injection prevention, and API key isolation.

### Running E2E Tests Locally
Run the full test suite with:
```bash
npm run test:e2e
```
Or directly using the Playwright CLI:
```bash
npx playwright test
```

### How Test Orchestration Works
- Playwright's `webServer` configuration automatically boots two local services:
  1. **FastAPI Test Backend** (`scripts/start_test_backend.py` on `http://127.0.0.1:8000`):
     - Uses a fresh, isolated temporary SQLite database (`pulsepay_playwright_test.db`).
     - Seeds a deterministic dataset: 15 payments across 2 pages, a payment with 3 webhook events (`PROCESSED`, `DUPLICATE_IGNORED`, `DELAYED_IGNORED`), and an XSS probe record containing `<script>alert(1)</script>`.
     - Injects a local test-only API key (`test-playwright-secret-key-xyz`).
     - **Never connects to the live Render deployment or any external network service.**
  2. **Next.js Production Server** (`npm run start -- -p 3000` on `http://127.0.0.1:3000`).
- Once test execution finishes, Playwright shuts down the local servers cleanly.

### Additional Playwright Options
- Run with interactive UI mode:
  ```bash
  npx playwright test --ui
  ```
- Run in headed browser mode:
  ```bash
  npx playwright test --headed
  ```
- View the HTML test report:
  ```bash
  npx playwright show-report
  ```
