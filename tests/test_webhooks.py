import uuid

def test_webhook_idempotency_duplicate_ignored(client, auth_headers):
    """
    Verify existing webhook idempotency behavior:
    1. First event processes and transitions payment to SUCCESS.
    2. Second event with identical event_id is safely ignored (DUPLICATE_IGNORED).
    """
    # 1. Create Invoice
    inv_payload = {
        "patient_id": "PAT-TEST-IDEM",
        "patient_name": "Diana Prince",
        "service_description": "Cardiology Checkup",
        "amount": 500.00
    }
    inv_res = client.post("/invoices", json=inv_payload, headers=auth_headers)
    assert inv_res.status_code == 201
    invoice_id = inv_res.json()["id"]

    # 2. Initiate Payment
    pay_payload = {
        "invoice_id": invoice_id,
        "amount": 500.00,
        "provider": "razorpay"
    }
    pay_res = client.post("/payments/create", json=pay_payload, headers=auth_headers)
    assert pay_res.status_code == 201
    payment_id = pay_res.json()["id"]

    # 3. Dispatch Webhook Event 1
    event_id = f"evt_idem_{uuid.uuid4().hex[:8]}"
    wh_payload = {
        "event_id": event_id,
        "payment_id": payment_id,
        "status": "SUCCESS"
    }
    wh_res_1 = client.post("/webhook/payment", json=wh_payload, headers=auth_headers)
    assert wh_res_1.status_code == 200
    assert wh_res_1.json()["status"] == "processed"

    # 4. Dispatch Identical Webhook (Duplicate Idempotency Test)
    wh_res_2 = client.post("/webhook/payment", json=wh_payload, headers=auth_headers)
    assert wh_res_2.status_code == 200
    assert wh_res_2.json()["status"] == "ignored"
    assert "Duplicate event_id" in wh_res_2.json()["message"]

    # 5. Verify payment detail reflects original webhook event
    detail_res = client.get(f"/payments/{payment_id}", headers=auth_headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["status"] == "SUCCESS"
    assert "PROCESSED" in detail["webhook_event_statuses"]
