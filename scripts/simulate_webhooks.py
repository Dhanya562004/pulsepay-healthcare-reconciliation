#!/usr/bin/env python3
"""
PulsePay Webhook & Payment API Simulation Script
Simulates gateway webhook payloads and verifies REST API capabilities:
1. Normal success webhook processing
2. Idempotency (duplicate event_id rejection)
3. Out-of-order delayed event handling
4. Unknown payment ID safe handling
5. Paginated payments list and payment detail retrieval
6. Financial reconciliation scan
"""

import requests
import json
import uuid
import time
import os
import sys

API_URL = os.getenv("API_URL", os.getenv("FASTAPI_BACKEND_URL", "http://localhost:8000"))
API_KEY = os.getenv("API_KEY", "")

def get_headers():
    headers = {}
    if API_KEY:
        headers["X-Api-Key"] = API_KEY
    return headers

def print_header(title):
    print("\n" + "="*70)
    print(f" [PULSEPAY] {title}")
    print("="*70)

def main():
    print_header("PULSEPAY WEBHOOK & API SIMULATION LAB")
    headers = get_headers()
    
    # Check if backend is alive (GET / is exempt from API key requirement)
    try:
        r = requests.get(f"{API_URL}/")
        if r.status_code != 200:
            print(f"[X] Backend at {API_URL} returned status {r.status_code}")
            sys.exit(1)
        print(f"[OK] Connected to PulsePay Backend at {API_URL}")
    except Exception as e:
        print(f"[X] Could not connect to PulsePay Backend at {API_URL}. Please start uvicorn backend.main:app first!")
        sys.exit(1)

    # Step 1: Create an Invoice
    print_header("1. CREATING TEST INVOICE")
    inv_payload = {
        "patient_id": f"PAT-SIM-{uuid.uuid4().hex[:4].upper()}",
        "patient_name": "Dr. Bruce Wayne",
        "service_description": "Orthopedic Surgery & Trauma Care",
        "amount": 3450.00
    }
    inv_res = requests.post(f"{API_URL}/invoices", json=inv_payload, headers=headers).json()
    invoice_id = inv_res["id"]
    print(f"Created Invoice ID: {invoice_id} | Amount: ${inv_res['amount']} | Status: {inv_res['status']}")

    # Step 2: Initiate Payment
    print_header("2. INITIATING PAYMENT GATEWAY TRANSACTION")
    pay_payload = {
        "invoice_id": invoice_id,
        "amount": 3450.00,
        "provider": "razorpay"
    }
    pay_res = requests.post(f"{API_URL}/payments/create", json=pay_payload, headers=headers).json()
    payment_id = pay_res["id"]
    print(f"Created Payment ID: {payment_id} | Status: {pay_res['status']} | Ext Ref: {pay_res['external_reference_id']}")

    # Step 3: Dispatch Normal Webhook
    print_header("3. DISPATCHING NORMAL SUCCESS WEBHOOK")
    event_id_1 = f"evt_sim_success_{uuid.uuid4().hex[:8]}"
    wh_payload_1 = {
        "event_id": event_id_1,
        "payment_id": payment_id,
        "status": "SUCCESS",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    wh_res_1 = requests.post(f"{API_URL}/webhook/payment", json=wh_payload_1, headers=headers).json()
    print("Webhook Response 1:")
    print(json.dumps(wh_res_1, indent=2))

    # Step 4: Dispatch Duplicate Webhook (Idempotency Test)
    print_header("4. TESTING IDEMPOTENCY (DISPATCHING DUPLICATE WEBHOOK)")
    print(f"Sending identical event_id '{event_id_1}' again...")
    wh_res_dup = requests.post(f"{API_URL}/webhook/payment", json=wh_payload_1, headers=headers).json()
    print("Duplicate Webhook Response:")
    print(json.dumps(wh_res_dup, indent=2))
    assert wh_res_dup["status"] == "ignored", "Expected status 'ignored' for duplicate event_id!"
    print("[OK] IDEMPOTENCY TEST PASSED! Duplicate event was correctly caught & ignored.")

    # Step 5: Dispatch Delayed Out-of-Order FAILED Webhook
    print_header("5. TESTING OUT-OF-ORDER DELAYED EVENT PROTECTION")
    event_id_delayed = f"evt_sim_delayed_{uuid.uuid4().hex[:8]}"
    wh_payload_delayed = {
        "event_id": event_id_delayed,
        "payment_id": payment_id,
        "status": "FAILED",
        "failure_reason": "Old delayed event from previous timeout",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    wh_res_delayed = requests.post(f"{API_URL}/webhook/payment", json=wh_payload_delayed, headers=headers).json()
    print("Delayed Webhook Response:")
    print(json.dumps(wh_res_delayed, indent=2))
    assert wh_res_delayed["status"] == "delayed_ignored", "Expected status 'delayed_ignored'!"
    print("[OK] OUT-OF-ORDER PROTECTION PASSED! Successful payment status was preserved.")

    # Step 6: Test Unknown Payment ID
    print_header("6. TESTING UNKNOWN PAYMENT ID SAFEHAVEN")
    unknown_pay_id = str(uuid.uuid4())
    event_id_unk = f"evt_sim_unk_{uuid.uuid4().hex[:8]}"
    wh_payload_unk = {
        "event_id": event_id_unk,
        "payment_id": unknown_pay_id,
        "status": "SUCCESS"
    }
    wh_res_unk = requests.post(f"{API_URL}/webhook/payment", json=wh_payload_unk, headers=headers).json()
    print("Unknown Payment Webhook Response:")
    print(json.dumps(wh_res_unk, indent=2))
    assert wh_res_unk["status"] == "payment_not_found", "Expected status 'payment_not_found'!"
    print("[OK] UNKNOWN PAYMENT TEST PASSED! Webhook handler did not crash.")

    # Step 7: Test Paginated Payments List & Payment Detail
    print_header("7. TESTING PAGINATED PAYMENTS & PAYMENT DETAIL")
    list_res = requests.get(f"{API_URL}/payments?limit=10&offset=0", headers=headers).json()
    assert "data" in list_res and "pagination" in list_res, "Expected paginated shape with 'data' and 'pagination'!"
    print(f"Paginated Payments Found: {len(list_res['data'])} | Total: {list_res['pagination']['total']} | hasMore: {list_res['pagination']['hasMore']}")

    detail_res = requests.get(f"{API_URL}/payments/{payment_id}", headers=headers).json()
    assert detail_res["id"] == payment_id, "Fetched payment detail ID mismatch!"
    assert "webhook_event_statuses" in detail_res, "Expected 'webhook_event_statuses' in payment detail!"
    print(f"Payment Detail Verified for {payment_id} | Statuses: {detail_res['webhook_event_statuses']}")
    print("[OK] PAGINATED PAYMENTS & DETAIL VERIFIED!")

    # Step 8: Run Reconciliation Scan
    print_header("8. RUNNING RECONCILIATION SCAN")
    recon_res = requests.get(f"{API_URL}/reconcile", headers=headers).json()
    print(f"Total Invoices Scanned: {recon_res['total_invoices_scanned']}")
    print(f"Total Payments Scanned: {recon_res['total_payments_scanned']}")
    print(f"Clean Invoices: {recon_res['clean_invoices']}")
    print(f"Total Mismatches Found: {recon_res['total_mismatches_found']}")

    print_header("ALL SIMULATION TESTS COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
