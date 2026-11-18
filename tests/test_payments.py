import uuid
from datetime import datetime
from backend.models.invoice import Invoice
from backend.models.payment import Payment
from backend.models.webhook import WebhookEvent

def create_sample_data(db, count=5):
    """Helper to seed invoices and payments for tests."""
    inv = Invoice(
        id=str(uuid.uuid4()),
        patient_id="PAT-TEST-001",
        patient_name="Bruce Wayne",
        service_description="Consultation",
        amount=1000.0,
        status="PENDING",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(inv)
    db.commit()

    payments = []
    statuses = ["SUCCESS", "FAILED", "INITIATED", "SUCCESS", "FAILED"]
    for i in range(count):
        st = statuses[i % len(statuses)]
        pay = Payment(
            id=str(uuid.uuid4()),
            invoice_id=inv.id,
            amount=200.0 + i * 10,
            status=st,
            provider="razorpay" if i % 2 == 0 else "stripe",
            external_reference_id=f"tx_test_{uuid.uuid4().hex[:8]}",
            failure_reason="Card declined" if st == "FAILED" else None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(pay)
        payments.append(pay)
    db.commit()
    return inv, payments

def test_payments_pagination_totals_and_has_more(client, db, auth_headers):
    """Verify limit, offset, total count and hasMore boolean computation."""
    inv, payments = create_sample_data(db, count=5)

    # Page 1: limit 2, offset 0 -> 2 items, total 5, hasMore True
    res = client.get("/payments?limit=2&offset=0", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert "data" in body and "pagination" in body
    assert len(body["data"]) == 2
    assert body["pagination"]["limit"] == 2
    assert body["pagination"]["offset"] == 0
    assert body["pagination"]["total"] == 5
    assert body["pagination"]["hasMore"] is True

    # Page 2: limit 2, offset 2 -> 2 items, total 5, hasMore True
    res = client.get("/payments?limit=2&offset=2", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert len(body["data"]) == 2
    assert body["pagination"]["offset"] == 2
    assert body["pagination"]["hasMore"] is True

    # Page 3: limit 2, offset 4 -> 1 item, total 5, hasMore False
    res = client.get("/payments?limit=2&offset=4", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert len(body["data"]) == 1
    assert body["pagination"]["offset"] == 4
    assert body["pagination"]["hasMore"] is False

    # Page with large limit: limit 10, offset 0 -> 5 items, total 5, hasMore False
    res = client.get("/payments?limit=10&offset=0", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert len(body["data"]) == 5
    assert body["pagination"]["total"] == 5
    assert body["pagination"]["hasMore"] is False

def test_payments_invalid_limit_returns_422(client, auth_headers):
    """Verify limit validation between 1 and 100 rejects bad values with HTTP 422."""
    # Limit 0 (below minimum 1)
    res = client.get("/payments?limit=0", headers=auth_headers)
    assert res.status_code == 422

    # Limit 101 (above maximum 100)
    res = client.get("/payments?limit=101", headers=auth_headers)
    assert res.status_code == 422

    # Negative limit
    res = client.get("/payments?limit=-5", headers=auth_headers)
    assert res.status_code == 422

    # Non-integer limit
    res = client.get("/payments?limit=abc", headers=auth_headers)
    assert res.status_code == 422

def test_payments_status_filter(client, db, auth_headers):
    """Verify optional status filter returns only matching payments and correct total."""
    inv, payments = create_sample_data(db, count=5)
    # Statuses in sample data: SUCCESS (2), FAILED (2), INITIATED (1)

    # Filter SUCCESS
    res = client.get("/payments?status=SUCCESS", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["pagination"]["total"] == 2
    for item in body["data"]:
        assert item["status"] == "SUCCESS"

    # Filter FAILED
    res = client.get("/payments?status=FAILED", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["pagination"]["total"] == 2
    for item in body["data"]:
        assert item["status"] == "FAILED"

    # Filter INITIATED
    res = client.get("/payments?status=INITIATED", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["pagination"]["total"] == 1
    assert body["data"][0]["status"] == "INITIATED"

def test_payment_detail_success(client, db, auth_headers):
    """Verify GET /payments/{id} returns payment details and webhook event statuses."""
    inv, payments = create_sample_data(db, count=1)
    target_pay = payments[0]

    # Attach related webhook events with various statuses
    wh1 = WebhookEvent(
        id=str(uuid.uuid4()),
        event_id=f"evt_1_{uuid.uuid4().hex[:6]}",
        payment_id=target_pay.id,
        status="SUCCESS",
        processing_status="PROCESSED",
        processed_at=datetime.utcnow()
    )
    wh2 = WebhookEvent(
        id=str(uuid.uuid4()),
        event_id=f"evt_2_{uuid.uuid4().hex[:6]}",
        payment_id=target_pay.id,
        status="SUCCESS",
        processing_status="DUPLICATE_IGNORED",
        processed_at=datetime.utcnow()
    )
    db.add_all([wh1, wh2])
    db.commit()

    res = client.get(f"/payments/{target_pay.id}", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()

    assert body["id"] == target_pay.id
    assert body["invoice_id"] == inv.id
    assert body["status"] == target_pay.status
    assert body["provider"] == target_pay.provider
    assert body["amount"] == target_pay.amount
    assert "created_at" in body
    assert "updated_at" in body
    assert "webhook_event_statuses" in body
    assert "PROCESSED" in body["webhook_event_statuses"]
    assert "DUPLICATE_IGNORED" in body["webhook_event_statuses"]

def test_payment_detail_not_found_404(client, auth_headers):
    """Verify unknown payment ID returns clean HTTP 404 with JSON error."""
    unknown_id = str(uuid.uuid4())
    res = client.get(f"/payments/{unknown_id}", headers=auth_headers)
    assert res.status_code == 404
    body = res.json()
    assert "detail" in body
    assert f"Payment '{unknown_id}' not found." in body["detail"]
