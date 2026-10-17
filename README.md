<div align="center">

# 🩺 PulsePay — Healthcare Billing, Payments & Reconciliation Engine

### *Production-Grade Financial Backend, Payment Gateway Integration & Real-Time Reconciliation System*

[![Live Streamlit App](https://img.shields.io/badge/🌐_Live_App-Streamlit_Cloud-00d2ff?style=for-the-badge&logo=streamlit&logoColor=white)](https://pulsepay-healthcare-reconciliation-fpyr9vynfto549zh8mwwhf.streamlit.app/)
[![Render Backend](https://img.shields.io/badge/⚡_Backend_API-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://pulsepay-backend-po8g.onrender.com)
[![Swagger API Docs](https://img.shields.io/badge/📖_API_Docs-Swagger_UI-85EA2D?style=for-the-badge&logo=swagger&logoColor=black)](https://pulsepay-backend-po8g.onrender.com/docs)
[![Python 3.13](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://neon.tech/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

<br>

| Service | Environment | Live URL |
| :--- | :--- | :--- |
| **🖥️ Executive Console** | Streamlit Cloud | [**Launch Live Dashboard**](https://pulsepay-healthcare-reconciliation-fpyr9vynfto549zh8mwwhf.streamlit.app/) |
| **⚡ REST API Service** | Render | [**https://pulsepay-backend-po8g.onrender.com**](https://pulsepay-backend-po8g.onrender.com) |
| **📑 Interactive API Docs** | Swagger / OpenAPI | [**https://pulsepay-backend-po8g.onrender.com/docs**](https://pulsepay-backend-po8g.onrender.com/docs) |
| **📚 Alternate API Specs** | ReDoc | [**https://pulsepay-backend-po8g.onrender.com/redoc**](https://pulsepay-backend-po8g.onrender.com/redoc) |

---

</div>

## 📌 Executive Summary

Healthcare financial systems process millions of billing invoices daily across third-party payment gateways (Razorpay, Stripe) and hospital management platforms. In real-world production environments, **network timeouts, out-of-order webhooks, duplicate event retries, and manual overrides** lead to critical discrepancies between gateway settlement logs and patient ledgers.

**PulsePay** is a production-grade healthcare reconciliation engine built to simulate, track, and automatically resolve real-world monetary flow failures. It guarantees **Strict Idempotency**, **Out-of-Order Webhook Protection**, **Sub-50ms Latency Observability**, and **5-Category Automated Financial Reconciliation**.

---

## ✨ Key Features & Technical Highlights

- 💳 **Healthcare Billing & Invoicing System:** UUID-indexed invoice creation, status tracking (`PENDING`, `PAID`, `FAILED`), and patient ledger history.
- 🔄 **Multi-Gateway Payment Integration:** Simulated payment gateway processor (Razorpay & Stripe mock) with failure simulation & automated/manual retry mechanics.
- 🛡️ **Production-Grade Webhook Engine:**
  - **Strict Idempotency:** Indexed `event_id` checking prevents duplicate event re-processing (`DUPLICATE_IGNORED`).
  - **Out-of-Order & Delayed Event Guard:** Discards delayed `FAILED` webhooks for already `SUCCESS` payments to prevent status corruption (`DELAYED_IGNORED`).
  - **Unknown Payment ID Safehaven:** Graceful fallback logging without throwing uncaught server exceptions (`PAYMENT_NOT_FOUND`).
  - **Double Update Prevention:** Atomic isolated database transactions using SQLAlchemy.
- 🔍 **5-Rule Financial Reconciliation Engine:** Detects and auto-resolves revenue discrepancies (Overpayments, Unretried Failures, Missing Payments).
- 🛰️ **Observability & Request Latency Middleware:** Computes execution duration in `ms` and attaches `X-Process-Time` tracing headers to all requests.
- 🎨 **Modern Streamlit Executive Dashboard:** Glassmorphic dark UI with real-time KPI cards, interactive Webhook Simulator Lab, and immutable audit logs.

---

## 🏗️ Architecture & Component Flow

```mermaid
graph TD
    UI["🖥️ Streamlit Cloud Dashboard<br>(Live Web App)"] -->|REST API Calls| API["⚡ FastAPI Backend Service<br>(Render Cloud)"]
    API -->|Latency Middleware| OBS["🛰️ Observability & Tracing Engine<br>(X-Process-Time)"]
    
    subgraph Core Business Services Layer
        API --> INV_S["📋 Invoice Service"]
        API --> PAY_S["💳 Payment Gateway Service"]
        API --> WH_S["🛡️ Webhook Ingestion Engine"]
        API --> REC_S["🔍 Financial Reconciliation Engine"]
        API --> AUD_S["📜 Audit & Telemetry Service"]
    end

    subgraph Production Failure & Idempotency Rules
        WH_S -->|Idempotency Check| IDEM["Unique event_id Index<br>(DUPLICATE_IGNORED)"]
        WH_S -->|Out-of-Order Guard| OO["Delayed Event Filter<br>(DELAYED_IGNORED)"]
        WH_S -->|Unknown Payment Guard| UP["Payment Not Found Handler<br>(PAYMENT_NOT_FOUND)"]
    end

    subgraph Cloud Persistence Layer
        INV_S --> ORM["SQLAlchemy ORM (Async-Ready)"]
        PAY_S --> ORM
        WH_S --> ORM
        REC_S --> ORM
        AUD_S --> ORM
        ORM --> DB[("🐘 Neon Serverless PostgreSQL / SQLite")]
    end
```

---

## ⚡ Production Webhook Edge Cases & Idempotency Rules

Webhooks in financial systems are inherently unpredictable. PulsePay handles all real-world failure modes:

| Scenario | Real-World Challenge | PulsePay Production Solution | Gateway Response |
| :--- | :--- | :--- | :--- |
| **Duplicate Event Retries** | Gateway retries same `event_id` multiple times due to timeout | Checked against `WebhookEvent.event_id` index; logged as `DUPLICATE_IGNORED` | `200 OK` (Ignored) |
| **Out-of-Order Events** | Delayed `FAILED` webhook arrives *after* payment achieved `SUCCESS` | Protects success state; logged as `DELAYED_IGNORED` | `200 OK` (Ignored) |
| **Unknown Payment ID** | Webhook payload references non-existent `payment_id` | Catches gracefully; logged as `PAYMENT_NOT_FOUND` without server crash | `200 OK` (Not Found) |
| **Concurrent Updates** | Simultaneous webhooks modifying invoice state | Atomic transaction isolation using SQLAlchemy session locks | `200 OK` (Processed) |

---

## 🔍 Reconciliation Engine & 5-Mismatch Detection

PulsePay scans all invoices and payment gateway records to flag **5 financial risk categories**:

```
 📊 FINANCIAL RECONCILIATION AUDIT
 ─────────────────────────────────────────────────────────────────────────────
 1. PAID_WITHOUT_SUCCESS_PAYMENT   [HIGH]     Invoice = PAID but no success payment
 2. SUCCESS_PAYMENT_INVOICE_PENDING[HIGH]     Payment = SUCCESS but Invoice = PENDING
 3. MULTIPLE_SUCCESS_PAYMENTS      [CRITICAL] Multiple payments for 1 invoice (Overpayment)
 4. UNRETRIED_FAILED_PAYMENT       [MEDIUM]   Failed payment attempts not retried
 5. AMOUNT_DISCREPANCY             [MEDIUM]   Paid amount != Invoice target amount
 ─────────────────────────────────────────────────────────────────────────────
```

---

## 📁 Repository Structure

```
pulsepay-healthcare-reconciliation/
│
├── app.py                             # Streamlit Executive Dashboard (Cloud & Local)
├── assets/
│   └── logo.png                       # High-res PulsePay brand logo asset
├── requirements.txt                   # Production dependencies
├── README.md                          # Comprehensive documentation & deployment guide
├── .env.example                       # Environment settings template
├── .gitignore                         # Git exclusion rules
│
├── backend/                           # Modular FastAPI Application
│   ├── main.py                        # FastAPI entrypoint, CORS & Observability Middleware
│   ├── config.py                      # Pydantic Settings & DB configuration
│   │
│   ├── database/                      # DB Engine & Session Provider
│   │   ├── base.py                    # SQLAlchemy Base
│   │   └── session.py                 # Engine setup (PostgreSQL / SQLite fallback)
│   │
│   ├── models/                        # SQLAlchemy ORM Models
│   │   ├── invoice.py                 # Invoice Table (id, patient_id, amount, status)
│   │   ├── payment.py                 # Payment Table (id, invoice_id, status, provider)
│   │   ├── webhook.py                 # WebhookEvent Table (event_id UNIQUE index)
│   │   └── audit.py                   # AuditLog Table (event_type, entity_id, timestamp)
│   │
│   ├── schemas/                       # Pydantic Schemas & Data Contracts
│   │   ├── invoice_schema.py
│   │   ├── payment_schema.py
│   │   ├── webhook_schema.py
│   │   ├── reconciliation_schema.py
│   │   └── audit_schema.py
│   │
│   ├── services/                      # Business Logic Layer (Clean Architecture)
│   │   ├── invoice_service.py         # Invoice CRUD & detail builder
│   │   ├── payment_service.py         # Payment gateway initiation & retries
│   │   ├── webhook_service.py         # Idempotent webhook processor
│   │   ├── reconciliation_service.py  # 5-rule financial mismatch scanner & resolver
│   │   └── audit_service.py           # Immutable audit logging & metrics
│   │
│   ├── routes/                        # FastAPI Controllers (Pure Route Handlers)
│   │   ├── invoice_routes.py          # /invoices API
│   │   ├── payment_routes.py          # /payments API
│   │   ├── webhook_routes.py          # /webhook/payment API
│   │   ├── reconciliation_routes.py   # /reconcile API
│   │   └── system_routes.py           # /metrics & /audit-logs API
│   │
│   └── utils/                         # Utilities & Middlewares
│       ├── logger.py                  # Structured console logger
│       ├── middleware.py              # Request latency & tracing middleware
│       └── seed.py                    # Healthcare billing seed dataset
│
└── scripts/
    └── simulate_webhooks.py           # CLI Webhook simulation & stress test script
```

---

## 🚀 Local Installation & Quick Start

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/Dhanya562004/pulsepay-healthcare-reconciliation.git
cd pulsepay-healthcare-reconciliation
pip install -r requirements.txt
```

### 2. Launch FastAPI Backend Server
```bash
uvicorn backend.main:app --reload --port 8000
```
- **Local Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Local ReDoc Specs:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 3. Launch Streamlit UI Dashboard
```bash
streamlit run app.py
```
- **Dashboard URL:** [http://localhost:8501](http://localhost:8501)

---

## 🧪 Webhook Simulation Lab

Run the automated test suite to verify idempotency, out-of-order protection, and reconciliation:

```bash
# Test against local server
python scripts/simulate_webhooks.py

# Or run against live Render backend
FASTAPI_BACKEND_URL=https://pulsepay-backend-po8g.onrender.com python scripts/simulate_webhooks.py
```

**Sample Output:**
```
======================================================================
 [PULSEPAY] PULSEPAY WEBHOOK SIMULATION LAB
======================================================================
[OK] Connected to PulsePay Backend at https://pulsepay-backend-po8g.onrender.com
Created Invoice ID: 7c7a2c5c-b071-40da-bfc1-ec83c381790a | Status: PENDING
Created Payment ID: a707a814-cb32-459d-a6cb-ee1ea5be207d | Status: INITIATED
[OK] Webhook processed successfully. Invoice status updated to 'PAID'.
[OK] IDEMPOTENCY TEST PASSED! Duplicate event was correctly caught & ignored.
[OK] OUT-OF-ORDER PROTECTION PASSED! Successful payment status was preserved.
[OK] UNKNOWN PAYMENT TEST PASSED! Webhook handler did not crash.
======================================================================
 [PULSEPAY] ALL SIMULATION TESTS COMPLETED SUCCESSFULLY!
======================================================================
```

---

## 📡 Live API Endpoints & cURL Examples

The backend is live at: `https://pulsepay-backend-po8g.onrender.com`

### 1. Health & Status Check (`GET /`)
```bash
curl -X GET "https://pulsepay-backend-po8g.onrender.com/"
```

### 2. System Metrics & KPIs (`GET /metrics`)
```bash
curl -X GET "https://pulsepay-backend-po8g.onrender.com/metrics"
```

### 3. Create Invoice (`POST /invoices`)
```bash
curl -X POST "https://pulsepay-backend-po8g.onrender.com/invoices" \
     -H "Content-Type: application/json" \
     -d '{
           "patient_id": "PAT-90210",
           "patient_name": "Sarah Connor",
           "service_description": "Brain MRI Scan & Radiology",
           "amount": 1250.00
         }'
```

### 4. Initiate Payment (`POST /payments/create`)
```bash
curl -X POST "https://pulsepay-backend-po8g.onrender.com/payments/create" \
     -H "Content-Type: application/json" \
     -d '{
           "invoice_id": "<INVOICE_UUID>",
           "amount": 1250.00,
           "provider": "razorpay"
         }'
```

### 5. Dispatch Webhook (`POST /webhook/payment`)
```bash
curl -X POST "https://pulsepay-backend-po8g.onrender.com/webhook/payment" \
     -H "Content-Type: application/json" \
     -d '{
           "event_id": "evt_live_test_998877",
           "payment_id": "<PAYMENT_UUID>",
           "status": "SUCCESS"
         }'
```

### 6. Run Financial Reconciliation (`GET /reconcile`)
```bash
curl -X GET "https://pulsepay-backend-po8g.onrender.com/reconcile"
```

### 7. Bulk Retry Failed Payments (`POST /payments/retry-all`)
```bash
curl -X POST "https://pulsepay-backend-po8g.onrender.com/payments/retry-all"
```

---

## ☁️ Deployment Architecture

- **Frontend:** [Streamlit Community Cloud](https://share.streamlit.io/) connected directly to GitHub repository (`app.py`).
- **Backend API:** [Render Web Service](https://render.com/) running FastAPI with auto-reload and Uvicorn workers.
- **Database:** [Neon Serverless PostgreSQL](https://neon.tech/) with pooled connections and SSL security.
- **CI/CD:** Pushes to `main` automatically trigger continuous deployment across Streamlit and Render.

---

## 🛡️ License

Built for real-world Healthcare Financial Infrastructure. Released under the **MIT License**.
