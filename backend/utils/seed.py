import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.models.invoice import Invoice
from backend.models.payment import Payment
from backend.models.webhook import WebhookEvent
from backend.models.audit import AuditLog
from backend.utils.logger import logger

def seed_sample_data(db: Session, force: bool = False):
    """
    Populates database with realistic healthcare billing, payment, webhook,
    and deliberate mismatch scenarios for testing reconciliation engine.
    """
    existing_count = db.query(Invoice).count()
    if existing_count > 0 and not force:
        logger.info(f"Database already contains {existing_count} invoices. Skipping seed.")
        return {"status": "skipped", "invoice_count": existing_count}

    if force:
        logger.info("Force flag passed. Clearing existing data...")
        db.query(AuditLog).delete()
        db.query(WebhookEvent).delete()
        db.query(Payment).delete()
        db.query(Invoice).delete()
        db.commit()

    logger.info("Seeding realistic healthcare billing & payment dataset...")
    now = datetime.utcnow()

    # 1. Standard Paid Invoice (Clean Flow)
    inv1 = Invoice(
        id=str(uuid.uuid4()),
        patient_id="PAT-1001",
        patient_name="Eleanor Vance",
        service_description="Brain MRI Scan with Contrast",
        amount=1250.00,
        status="PAID",
        created_at=now - timedelta(days=5),
        updated_at=now - timedelta(days=5)
    )
    pay1 = Payment(
        id=str(uuid.uuid4()),
        invoice_id=inv1.id,
        amount=1250.00,
        status="SUCCESS",
        provider="stripe",
        external_reference_id=f"tx_stripe_{uuid.uuid4().hex[:10]}",
        created_at=now - timedelta(days=5),
        updated_at=now - timedelta(days=5)
    )
    evt1 = WebhookEvent(
        id=str(uuid.uuid4()),
        event_id=f"evt_stripe_{uuid.uuid4().hex[:12]}",
        payment_id=pay1.id,
        status="SUCCESS",
        processing_status="PROCESSED",
        payload='{"status": "SUCCESS", "provider": "stripe"}',
        processed_at=now - timedelta(days=5)
    )

    # 2. Pending Invoice (No Payment Yet)
    inv2 = Invoice(
        id=str(uuid.uuid4()),
        patient_id="PAT-1002",
        patient_name="Arthur Pendelton",
        service_description="Outpatient Cardiac Consultation",
        amount=350.00,
        status="PENDING",
        created_at=now - timedelta(days=3),
        updated_at=now - timedelta(days=3)
    )

    # 3. Mismatch Scenario A: Payment SUCCESS but Invoice still PENDING (Delayed Webhook / Webhook Failure)
    inv3 = Invoice(
        id=str(uuid.uuid4()),
        patient_id="PAT-1003",
        patient_name="Clara Oswald",
        service_description="Emergency Trauma Care & X-Ray",
        amount=2800.00,
        status="PENDING", # Mismatch!
        created_at=now - timedelta(days=2),
        updated_at=now - timedelta(days=2)
    )
    pay3 = Payment(
        id=str(uuid.uuid4()),
        invoice_id=inv3.id,
        amount=2800.00,
        status="SUCCESS",
        provider="razorpay",
        external_reference_id=f"pay_rzp_{uuid.uuid4().hex[:10]}",
        created_at=now - timedelta(days=2),
        updated_at=now - timedelta(days=2)
    )

    # 4. Mismatch Scenario B: Invoice PAID but NO Success Payment (Data Corruption / Manual Override)
    inv4 = Invoice(
        id=str(uuid.uuid4()),
        patient_id="PAT-1004",
        patient_name="Marcus Aurelius",
        service_description="Physiotherapy & Rehabilitation",
        amount=600.00,
        status="PAID", # Mismatch!
        created_at=now - timedelta(days=4),
        updated_at=now - timedelta(days=4)
    )

    # 5. Mismatch Scenario C: Failed Payment Not Retried
    inv5 = Invoice(
        id=str(uuid.uuid4()),
        patient_id="PAT-1005",
        patient_name="Diana Prince",
        service_description="Full Blood Panel & Metabolic Panel",
        amount=420.00,
        status="FAILED",
        created_at=now - timedelta(days=1),
        updated_at=now - timedelta(days=1)
    )
    pay5 = Payment(
        id=str(uuid.uuid4()),
        invoice_id=inv5.id,
        amount=420.00,
        status="FAILED",
        provider="stripe",
        external_reference_id=f"tx_stripe_{uuid.uuid4().hex[:10]}",
        failure_reason="Card limit exceeded / Declined by bank",
        created_at=now - timedelta(days=1),
        updated_at=now - timedelta(days=1)
    )

    # 6. Mismatch Scenario D: Multiple Success Payments (Overpayment / Double Charge)
    inv6 = Invoice(
        id=str(uuid.uuid4()),
        patient_id="PAT-1006",
        patient_name="Bruce Wayne",
        service_description="Orthopedic Surgery Consultation",
        amount=1500.00,
        status="PAID",
        created_at=now - timedelta(days=6),
        updated_at=now - timedelta(days=6)
    )
    pay6_a = Payment(
        id=str(uuid.uuid4()),
        invoice_id=inv6.id,
        amount=1500.00,
        status="SUCCESS",
        provider="razorpay",
        external_reference_id=f"pay_rzp_{uuid.uuid4().hex[:10]}",
        created_at=now - timedelta(days=6),
        updated_at=now - timedelta(days=6)
    )
    pay6_b = Payment(
        id=str(uuid.uuid4()),
        invoice_id=inv6.id,
        amount=1500.00,
        status="SUCCESS",
        provider="stripe",
        external_reference_id=f"tx_stripe_{uuid.uuid4().hex[:10]}",
        created_at=now - timedelta(days=6, hours=1),
        updated_at=now - timedelta(days=6, hours=1)
    )

    # Add all entities to session
    db.add_all([inv1, inv2, inv3, inv4, inv5, inv6])
    db.add_all([pay1, pay3, pay5, pay6_a, pay6_b])
    db.add_all([evt1])

    # Add audit log
    audit_seed = AuditLog(
        id=str(uuid.uuid4()),
        event_type="SYSTEM_SEED",
        entity_type="SYSTEM",
        message="Seeded 6 healthcare invoices, payments, and mismatch scenarios into database.",
        timestamp=now
    )
    db.add(audit_seed)
    db.commit()

    logger.info("Database seeding completed successfully.")
    return {
        "status": "success",
        "invoices_created": 6,
        "payments_created": 5,
        "webhooks_created": 1
    }
