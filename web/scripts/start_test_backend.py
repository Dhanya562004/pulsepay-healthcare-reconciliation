#!/usr/bin/env python3
"""
Test backend runner for Playwright E2E testing.
Initializes an isolated temporary SQLite database, seeds realistic payments
(including pagination targets, webhook timelines, and XSS safety checks),
and launches the FastAPI server on port 8000 using a test-only API key.
"""

import os
import sys
import tempfile
import uuid
from datetime import datetime, timedelta

# Ensure repo root is in python module search path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# Configure Test Environment Variables
TEST_API_KEY = os.getenv("API_KEY", "test-playwright-secret-key-xyz")
TEMP_DB_PATH = os.path.join(tempfile.gettempdir(), "pulsepay_playwright_test.db")

# Reset previous test database if present
if os.path.exists(TEMP_DB_PATH):
    try:
        os.remove(TEMP_DB_PATH)
    except Exception:
        pass

os.environ["DATABASE_URL"] = f"sqlite:///{TEMP_DB_PATH}"
os.environ["ENVIRONMENT"] = "test"
os.environ["API_KEY"] = TEST_API_KEY
os.environ["CORS_ALLOWED_ORIGINS"] = "http://localhost:3000,http://127.0.0.1:3000"

from backend.database.base import Base
from backend.database.session import engine, SessionLocal
from backend.models.invoice import Invoice
from backend.models.payment import Payment
from backend.models.webhook import WebhookEvent
from backend.main import create_app
import uvicorn

# Deterministic UUIDs for E2E assertions
DETAIL_PAYMENT_ID = "11111111-1111-1111-1111-111111111111"
DETAIL_INVOICE_ID = "aaaa1111-1111-1111-1111-111111111111"

XSS_PAYMENT_ID = "22222222-2222-2222-2222-222222222222"
XSS_INVOICE_ID = "bbbb2222-2222-2222-2222-222222222222"

def seed_playwright_dataset():
    """Seed test database with 15 payments to exercise pagination, detail, and XSS rendering."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        now = datetime.utcnow()

        # 1. Primary Payment for Detail Page & Webhook Timeline test
        inv_detail = Invoice(
            id=DETAIL_INVOICE_ID,
            patient_id="PAT-9001",
            patient_name="Arthur Dent",
            service_description="Neurology Diagnostics & MRI",
            amount=1250.00,
            status="PAID",
            created_at=now - timedelta(days=2),
            updated_at=now - timedelta(days=2)
        )
        pay_detail = Payment(
            id=DETAIL_PAYMENT_ID,
            invoice_id=DETAIL_INVOICE_ID,
            amount=1250.00,
            status="SUCCESS",
            provider="stripe",
            external_reference_id="tx_stripe_detail_001",
            failure_reason=None,
            created_at=now - timedelta(days=2),
            updated_at=now - timedelta(days=2)
        )
        wh_processed = WebhookEvent(
            id=str(uuid.uuid4()),
            event_id="evt_processed_001",
            payment_id=DETAIL_PAYMENT_ID,
            status="SUCCESS",
            processing_status="PROCESSED",
            payload='{"status": "SUCCESS", "event": "payment.succeeded"}',
            processed_at=now - timedelta(days=2)
        )
        wh_dup = WebhookEvent(
            id=str(uuid.uuid4()),
            event_id="evt_duplicate_002",
            payment_id=DETAIL_PAYMENT_ID,
            status="SUCCESS",
            processing_status="DUPLICATE_IGNORED",
            payload='{"status": "SUCCESS", "duplicate": true}',
            processed_at=now - timedelta(days=1, hours=23)
        )
        wh_delayed = WebhookEvent(
            id=str(uuid.uuid4()),
            event_id="evt_delayed_003",
            payment_id=DETAIL_PAYMENT_ID,
            status="FAILED",
            processing_status="DELAYED_IGNORED",
            payload='{"status": "FAILED", "delayed": true}',
            processed_at=now - timedelta(days=1, hours=22)
        )

        # 2. Payment containing XSS probe in provider and failure reason
        inv_xss = Invoice(
            id=XSS_INVOICE_ID,
            patient_id="PAT-XSS-001",
            patient_name="XSS Testing Patient",
            service_description="Sanitization Verification",
            amount=500.00,
            status="FAILED",
            created_at=now - timedelta(days=1),
            updated_at=now - timedelta(days=1)
        )
        pay_xss = Payment(
            id=XSS_PAYMENT_ID,
            invoice_id=XSS_INVOICE_ID,
            amount=500.00,
            status="FAILED",
            provider="<script>alert(1)</script>",
            external_reference_id="tx_xss_probe_001",
            failure_reason="Card error: <script>alert(1)</script>",
            created_at=now - timedelta(days=1),
            updated_at=now - timedelta(days=1)
        )

        db.add_all([inv_detail, pay_detail, wh_processed, wh_dup, wh_delayed])
        db.add_all([inv_xss, pay_xss])

        # 3. Add 13 more payments with mixed statuses to make total = 15 payments
        # Page 1 (limit 10) will contain 10 payments (hasMore: True)
        # Page 2 (offset 10) will contain remaining 5 payments (hasMore: False)
        statuses = ["SUCCESS", "FAILED", "INITIATED"]
        providers = ["razorpay", "stripe"]
        for i in range(3, 16):
            inv_id = f"inv-seq-{i:04d}"
            pay_id = f"pay-seq-{i:04d}-{uuid.uuid4().hex[:8]}"
            st = statuses[i % len(statuses)]
            prov = providers[i % len(providers)]

            inv = Invoice(
                id=inv_id,
                patient_id=f"PAT-SEQ-{i:04d}",
                patient_name=f"Patient Sequence {i}",
                service_description="Routine Medical Checkup",
                amount=100.00 * i,
                status="PAID" if st == "SUCCESS" else ("FAILED" if st == "FAILED" else "PENDING"),
                created_at=now - timedelta(hours=i * 2),
                updated_at=now - timedelta(hours=i * 2)
            )
            pay = Payment(
                id=pay_id,
                invoice_id=inv_id,
                amount=100.00 * i,
                status=st,
                provider=prov,
                external_reference_id=f"tx_seq_{i:04d}_{uuid.uuid4().hex[:6]}",
                failure_reason="Bank network timeout" if st == "FAILED" else None,
                created_at=now - timedelta(hours=i * 2),
                updated_at=now - timedelta(hours=i * 2)
            )
            db.add_all([inv, pay])

        db.commit()
        print(f"[TEST BACKEND] Successfully seeded 15 payments into {TEMP_DB_PATH}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_playwright_dataset()
    app = create_app()
    print(f"[TEST BACKEND] Starting FastAPI on 127.0.0.1:8000 (API_KEY={TEST_API_KEY[:4]}***)...")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
