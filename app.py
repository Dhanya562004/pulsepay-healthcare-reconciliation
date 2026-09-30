import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
import uuid
import time
from datetime import datetime

# Import backend services for fallback / embedded mode (essential for Streamlit Cloud deployment)
try:
    from backend.database.session import SessionLocal, engine
    from backend.database.base import Base
    from backend.services.invoice_service import InvoiceService
    from backend.services.payment_service import PaymentService
    from backend.services.webhook_service import WebhookService
    from backend.services.reconciliation_service import ReconciliationService
    from backend.services.audit_service import AuditService
    from backend.schemas.invoice_schema import InvoiceCreate
    from backend.schemas.payment_schema import PaymentCreate
    from backend.schemas.webhook_schema import WebhookPayload
    from backend.utils.seed import seed_sample_data
    
    # Initialize DB tables for embedded fallback mode
    Base.metadata.create_all(bind=engine)
    HAS_BACKEND_MODULES = True
except Exception as e:
    HAS_BACKEND_MODULES = False

# Configuration
API_BASE_URL = st.sidebar.text_input("FastAPI Backend URL", value="http://localhost:8000")

# Page Config
st.set_page_config(
    page_title="PulsePay — Healthcare Reconciliation Engine",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Modern Custom CSS (Dark Theme, Glassmorphism, Micro-animations)
st.markdown("""
<style>
    /* Global Styles */
    .stApp {
        background: linear-gradient(135deg, #0b0f19 0%, #111827 50%, #0d1322 100%);
        color: #f3f4f6;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    
    /* Header Banner */
    .main-header {
        background: linear-gradient(90deg, rgba(14, 165, 233, 0.15) 0%, rgba(99, 102, 241, 0.15) 100%);
        border: 1px solid rgba(56, 189, 248, 0.2);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    
    .main-header h1 {
        color: #f8fafc;
        font-weight: 800;
        font-size: 2.2rem;
        margin: 0;
        background: linear-gradient(90deg, #38bdf8 0%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .main-header p {
        color: #94a3b8;
        font-size: 1.05rem;
        margin-top: 6px;
        margin-bottom: 0;
    }

    /* Metric Card Styling */
    .metric-card {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        backdrop-filter: blur(8px);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(56, 189, 248, 0.4);
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #38bdf8;
        margin-top: 4px;
    }
    .metric-label {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94a3b8;
    }

    /* Badge Customizations */
    .badge-paid {
        background-color: rgba(34, 197, 94, 0.2);
        color: #4ade80;
        border: 1px solid rgba(34, 197, 94, 0.4);
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .badge-pending {
        background-color: rgba(234, 179, 8, 0.2);
        color: #facc15;
        border: 1px solid rgba(234, 179, 8, 0.4);
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .badge-failed {
        background-color: rgba(239, 68, 68, 0.2);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.4);
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    
    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to query backend via REST API or direct fallback
def check_fastapi_connection():
    try:
        resp = requests.get(f"{API_BASE_URL}/", timeout=1.5)
        if resp.status_code == 200:
            return True
    except Exception:
        pass
    return False

IS_API_CONNECTED = check_fastapi_connection()

# Sidebar Setup
st.sidebar.image("https://img.icons8.com/isometric-line/96/health-calendar.png", width=64)
st.sidebar.title("PulsePay Console")
st.sidebar.caption("Healthcare Billing & Reconciliation")

if IS_API_CONNECTED:
    st.sidebar.success(f"🟢 Connected to FastAPI Server\n(`{API_BASE_URL}`)")
else:
    st.sidebar.warning("⚡ Embedded Engine Mode\n(Direct DB Fallback Active)")

nav_selection = st.sidebar.radio(
    "Navigation",
    [
        "📊 System Overview",
        "📋 Invoices & Billing",
        "💳 Payment Gateway",
        "🧪 Webhook Simulator Lab",
        "🔍 Reconciliation Engine",
        "🛰️ Observability & Audits"
    ]
)

st.sidebar.markdown("---")
st.sidebar.subheader("Quick Actions")
if st.sidebar.button("🔄 Seed / Reset Dataset", use_container_width=True):
    if IS_API_CONNECTED:
        r = requests.post(f"{API_BASE_URL}/seed?force=true")
        st.sidebar.toast("Database seeded via REST API!", icon="✅")
    elif HAS_BACKEND_MODULES:
        db = SessionLocal()
        try:
            seed_sample_data(db, force=True)
            st.sidebar.toast("Database seeded in direct DB mode!", icon="✅")
        finally:
            db.close()
    st.rerun()

# -------------------------------------------------------------------
# DATA RETRIEVAL HELPERS
# -------------------------------------------------------------------
def get_metrics_data():
    if IS_API_CONNECTED:
        res = requests.get(f"{API_BASE_URL}/metrics").json()
        return res
    elif HAS_BACKEND_MODULES:
        db = SessionLocal()
        try:
            return AuditService.get_system_metrics(db)
        finally:
            db.close()
    return {}

def get_invoices_list(status_filter=None):
    if IS_API_CONNECTED:
        params = {}
        if status_filter and status_filter != "ALL":
            params["status"] = status_filter
        res = requests.get(f"{API_BASE_URL}/invoices", params=params).json()
        return res
    elif HAS_BACKEND_MODULES:
        db = SessionLocal()
        try:
            items = InvoiceService.get_invoices(db, status=status_filter if status_filter != "ALL" else None)
            return [i.to_dict() for i in items]
        finally:
            db.close()
    return []

# ===================================================================
# 1. SYSTEM OVERVIEW DASHBOARD
# ===================================================================
if nav_selection == "📊 System Overview":
    st.markdown("""
    <div class="main-header">
        <h1>🩺 PulsePay Reconciliation Dashboard</h1>
        <p>Production-grade financial engine for healthcare billing, multi-gateway payments, idempotency & reconciliation.</p>
    </div>
    """, unsafe_allow_html=True)

    metrics = get_metrics_data()
    if metrics:
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Total Invoiced</div>
                <div class="metric-value">${metrics.get('total_invoiced_amount', 0):,.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Total Collected</div>
                <div class="metric-value" style="color: #4ade80;">${metrics.get('total_collected_amount', 0):,.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Pending Balance</div>
                <div class="metric-value" style="color: #facc15;">${metrics.get('total_pending_amount', 0):,.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Duplicate Webhooks Blocked</div>
                <div class="metric-value" style="color: #a78bfa;">{metrics.get('duplicate_webhooks_blocked', 0)}</div>
            </div>
            """, unsafe_allow_html=True)
        with col5:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Total Webhooks Processed</div>
                <div class="metric-value" style="color: #38bdf8;">{metrics.get('total_webhooks', 0)}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Charts Section
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Invoice Billing Status Breakdown")
            status_counts = metrics.get('invoice_status_counts', {})
            if status_counts:
                df_status = pd.DataFrame([{"Status": k, "Count": v} for k, v in status_counts.items()])
                fig_status = px.pie(
                    df_status, names="Status", values="Count",
                    hole=0.4,
                    color="Status",
                    color_discrete_map={"PAID": "#4ade80", "PENDING": "#facc15", "FAILED": "#f87171"}
                )
                fig_status.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#f3f4f6")
                st.plotly_chart(fig_status, use_container_width=True)
            else:
                st.info("No invoice status data available.")

        with c2:
            st.subheader("Payment Gateway Status Distribution")
            pay_counts = metrics.get('payment_status_counts', {})
            if pay_counts:
                df_pay = pd.DataFrame([{"Gateway Status": k, "Count": v} for k, v in pay_counts.items()])
                fig_pay = px.bar(
                    df_pay, x="Gateway Status", y="Count",
                    color="Gateway Status",
                    color_discrete_map={"SUCCESS": "#4ade80", "INITIATED": "#38bdf8", "FAILED": "#f87171"}
                )
                fig_pay.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#f3f4f6")
                st.plotly_chart(fig_pay, use_container_width=True)
            else:
                st.info("No payment status data available.")

# ===================================================================
# 2. INVOICES & BILLING MANAGEMENT
# ===================================================================
elif nav_selection == "📋 Invoices & Billing":
    st.title("📋 Healthcare Billing & Invoices")

    tab1, tab2 = st.tabs(["View & Filter Invoices", "➕ Create New Invoice"])

    with tab1:
        st.subheader("Invoice Explorer")
        status_filter = st.selectbox("Filter by Status", ["ALL", "PENDING", "PAID", "FAILED"])
        invoices = get_invoices_list(status_filter)

        if invoices:
            df_inv = pd.DataFrame(invoices)
            st.dataframe(
                df_inv[["id", "patient_id", "patient_name", "service_description", "amount", "status", "created_at"]],
                use_container_width=True,
                column_config={
                    "amount": st.column_config.NumberColumn("Amount ($)", format="$%.2f"),
                    "created_at": st.column_config.DatetimeColumn("Date Created", format="YYYY-MM-DD HH:mm")
                }
            )
        else:
            st.info("No invoices found.")

    with tab2:
        st.subheader("Generate New Healthcare Invoice")
        with st.form("create_invoice_form"):
            c1, c2 = st.columns(2)
            with c1:
                patient_id = st.text_input("Patient ID", value=f"PAT-{uuid.uuid4().hex[:5].upper()}")
                patient_name = st.text_input("Patient Full Name", value="Sarah Connor")
            with c2:
                service_desc = st.selectbox(
                    "Medical Service Description",
                    [
                        "MRI Brain Scan & Contrast",
                        "Cardiovascular Workup",
                        "Orthopedic Surgery Consultation",
                        "Routine Lab Bloodwork Panel",
                        "Emergency ER Suite Visit",
                        "Outpatient General Consultation"
                    ]
                )
                amount = st.number_input("Invoice Amount ($USD)", min_value=10.0, max_value=50000.0, value=750.0, step=50.0)

            submitted = st.form_submit_button("Generate Invoice", use_container_width=True)
            if submitted:
                payload = {
                    "patient_id": patient_id,
                    "patient_name": patient_name,
                    "service_description": service_desc,
                    "amount": amount
                }
                if IS_API_CONNECTED:
                    res = requests.post(f"{API_BASE_URL}/invoices", json=payload)
                    if res.status_code == 201:
                        st.success(f"Invoice created successfully! ID: `{res.json()['id']}`")
                        st.rerun()
                elif HAS_BACKEND_MODULES:
                    db = SessionLocal()
                    try:
                        inv_data = InvoiceCreate(**payload)
                        created = InvoiceService.create_invoice(db, inv_data)
                        st.success(f"Invoice created! ID: `{created.id}`")
                        st.rerun()
                    finally:
                        db.close()

# ===================================================================
# 3. PAYMENT GATEWAY PROCESSING
# ===================================================================
elif nav_selection == "💳 Payment Gateway":
    st.title("💳 Simulated Payment Gateway")
    st.caption("Process payments via simulated Razorpay / Stripe integrations and handle failure retries.")

    invoices = get_invoices_list("ALL")
    pending_invoices = [i for i in invoices if i["status"] in ["PENDING", "FAILED"]]

    col1, col2 = st.columns([1.2, 1])

    with col1:
        st.subheader("Initiate Payment Transaction")
        if pending_invoices:
            inv_map = {f"{i['patient_name']} (ID: {i['id'][:8]}...) - ${i['amount']:.2f} [{i['status']}]": i for i in pending_invoices}
            selected_inv_label = st.selectbox("Select Target Invoice", list(inv_map.keys()))
            target_inv = inv_map[selected_inv_label]

            provider = st.radio("Payment Gateway Provider", ["razorpay", "stripe"], horizontal=True)
            simulate_failure = st.checkbox("Simulate Gateway Network Failure / Card Decline", value=False)

            if st.button("🚀 Process Payment", use_container_width=True):
                payload = {
                    "invoice_id": target_inv["id"],
                    "amount": target_inv["amount"],
                    "provider": provider,
                    "simulate_failure": simulate_failure
                }
                if IS_API_CONNECTED:
                    res = requests.post(f"{API_BASE_URL}/payments/create", json=payload)
                    if res.status_code == 201:
                        p_data = res.json()
                        st.success(f"Payment {p_data['status']}! Ref: `{p_data['external_reference_id']}`")
                        st.rerun()
                elif HAS_BACKEND_MODULES:
                    db = SessionLocal()
                    try:
                        p_create = PaymentCreate(**payload)
                        res = PaymentService.create_payment(db, p_create)
                        st.success(f"Payment {res['status']}! Ref: `{res['external_reference_id']}`")
                        st.rerun()
                    finally:
                        db.close()
        else:
            st.info("No pending or failed invoices available for payment.")

    with col2:
        st.subheader("Failure Recovery & Retry System")
        st.write("Trigger automated retry attempts for failed transactions.")

        if st.button("🔄 Bulk Retry All Failed Payments", use_container_width=True):
            if IS_API_CONNECTED:
                res = requests.post(f"{API_BASE_URL}/payments/retry-all").json()
                st.success(f"Bulk retry completed! Retried: {res['total_retried']} | Succeeded: {res['succeeded']}")
                st.rerun()
            elif HAS_BACKEND_MODULES:
                db = SessionLocal()
                try:
                    res = PaymentService.retry_all_failed_payments(db)
                    st.success(f"Bulk retry completed! Retried: {res['total_retried']} | Succeeded: {res['succeeded']}")
                    st.rerun()
                finally:
                    db.close()

# ===================================================================
# 4. WEBHOOK SIMULATOR LAB
# ===================================================================
elif nav_selection == "🧪 Webhook Simulator Lab":
    st.title("🧪 Production Webhook Testing Lab")
    st.markdown("""
    Test real-world webhook edge cases: **Idempotency (Duplicate event_id)**, **Out-of-Order / Delayed Events**, and **Unknown Payment IDs**.
    """)

    # Get payments list for dropdown
    all_invoices = get_invoices_list("ALL")
    payments_list = []
    if IS_API_CONNECTED:
        # fetch payments via invoice detail or audit
        for inv in all_invoices:
            d = requests.get(f"{API_BASE_URL}/invoices/{inv['id']}").json()
            payments_list.extend(d.get("payments", []))
    elif HAS_BACKEND_MODULES:
        db = SessionLocal()
        try:
            for inv in all_invoices:
                d = InvoiceService.get_invoice_detail(db, inv['id'])
                if d:
                    payments_list.extend(d.get("payments", []))
        finally:
            db.close()

    c1, c2 = st.columns([1, 1])

    with c1:
        st.subheader("Webhook Payload Generator")
        
        preset = st.selectbox(
            "Select Test Scenario Preset",
            [
                "Custom Manual Payload",
                "Scenario A: Normal Success Webhook",
                "Scenario B: Duplicate Webhook (Idempotency Test)",
                "Scenario C: Delayed FAILED Webhook (Out-of-Order)",
                "Scenario D: Unknown Payment ID"
            ]
        )

        default_event_id = f"evt_{uuid.uuid4().hex[:10]}"
        default_pay_id = payments_list[0]["id"] if payments_list else str(uuid.uuid4())
        default_status = "SUCCESS"

        if preset == "Scenario B: Duplicate Webhook (Idempotency Test)":
            default_event_id = "evt_duplicate_test_998877"
        elif preset == "Scenario C: Delayed FAILED Webhook (Out-of-Order)":
            default_status = "FAILED"
        elif preset == "Scenario D: Unknown Payment ID":
            default_pay_id = f"pay_unknown_{uuid.uuid4().hex[:8]}"

        event_id = st.text_input("Webhook Event ID (unique)", value=default_event_id)
        payment_id = st.text_input("Target Payment ID", value=default_pay_id)
        wh_status = st.selectbox("Gateway Event Status", ["SUCCESS", "FAILED"], index=0 if default_status == "SUCCESS" else 1)
        failure_reason = st.text_input("Failure Reason (if FAILED)", value="Insufficient Funds / Invalid CVV") if wh_status == "FAILED" else None

        if st.button("📡 Dispatch Webhook to Endpoint", use_container_width=True):
            payload = {
                "event_id": event_id,
                "payment_id": payment_id,
                "status": wh_status,
                "failure_reason": failure_reason,
                "timestamp": datetime.utcnow().isoformat()
            }
            start_t = time.time()
            if IS_API_CONNECTED:
                res = requests.post(f"{API_BASE_URL}/webhook/payment", json=payload)
                resp_json = res.json()
            elif HAS_BACKEND_MODULES:
                db = SessionLocal()
                try:
                    wh_p = WebhookPayload(**payload)
                    res_obj = WebhookService.process_payment_webhook(db, wh_p)
                    resp_json = res_obj.model_dump()
                finally:
                    db.close()
            
            dur = (time.time() - start_t) * 1000

            st.markdown("### Webhook Dispatch Result")
            st.json(resp_json)
            st.info(f"⏱️ Total Webhook Processing Latency: `{dur:.2f}ms`")

    with c2:
        st.subheader("Webhook Event Ingestion Log")
        if IS_API_CONNECTED:
            history = requests.get(f"{API_BASE_URL}/webhook/history").json()
        elif HAS_BACKEND_MODULES:
            db = SessionLocal()
            try:
                history = [e.to_dict() for e in WebhookService.get_webhook_history(db)]
            finally:
                db.close()
        else:
            history = []

        if history:
            df_wh = pd.DataFrame(history)
            st.dataframe(
                df_wh[["event_id", "payment_id", "status", "processing_status", "processed_at"]],
                use_container_width=True
            )
        else:
            st.info("No webhook event history logged.")

# ===================================================================
# 5. RECONCILIATION ENGINE
# ===================================================================
elif nav_selection == "🔍 Reconciliation Engine":
    st.title("🔍 Healthcare Financial Reconciliation Engine")
    st.markdown("""
    Automated mismatch detector analyzing invoices vs payment gateway records across 5 financial risk categories.
    """)

    if st.button("⚡ Run Full System Reconciliation Scan", use_container_width=True):
        st.rerun()

    report = None
    if IS_API_CONNECTED:
        report = requests.get(f"{API_BASE_URL}/reconcile").json()
    elif HAS_BACKEND_MODULES:
        db = SessionLocal()
        try:
            report_obj = ReconciliationService.run_reconciliation(db)
            report = report_obj.model_dump()
        finally:
            db.close()

    if report:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Invoices Scanned", report.get("total_invoices_scanned", 0))
        c2.metric("Payments Scanned", report.get("total_payments_scanned", 0))
        c3.metric("Clean Invoices", report.get("clean_invoices", 0), delta="Reconciled")
        c4.metric("Mismatches Found", report.get("total_mismatches_found", 0), delta="-Mismatches", delta_color="inverse")

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Detected Financial Mismatches")

        mismatches = report.get("mismatches", [])
        if mismatches:
            for idx, m in enumerate(mismatches):
                severity_color = "#f87171" if m["severity"] in ["HIGH", "CRITICAL"] else "#facc15"
                with st.expander(f"⚠️ [{m['severity']}] {m['mismatch_type']} — Patient: {m['patient_name']} (Inv: {m['invoice_id'][:8]}...)"):
                    st.markdown(f"**Description:** {m['description']}")
                    st.markdown(f"**Suggested Resolution:** `{m['suggested_action']}`")
                    st.json(m['details'])

                    if st.button(f"🛠️ Auto-Resolve Mismatch #{idx+1}", key=f"fix_{idx}"):
                        if IS_API_CONNECTED:
                            r = requests.post(f"{API_BASE_URL}/reconcile/resolve?invoice_id={m['invoice_id']}&mismatch_type={m['mismatch_type']}").json()
                            st.success(f"Resolved! {r.get('resolution_notes')}")
                            st.rerun()
                        elif HAS_BACKEND_MODULES:
                            db = SessionLocal()
                            try:
                                r = ReconciliationService.resolve_mismatch(db, m['invoice_id'], m['mismatch_type'])
                                st.success(f"Resolved! {r.get('resolution_notes')}")
                                st.rerun()
                            finally:
                                db.close()
        else:
            st.success("🎉 All invoices and payment gateway records are 100% cleanly reconciled!")

# ===================================================================
# 6. OBSERVABILITY & SYSTEM AUDITS
# ===================================================================
elif nav_selection == "🛰️ Observability & Audits":
    st.title("🛰️ Observability, Latency Telemetry & System Audits")

    t1, t2 = st.tabs(["📜 System Audit Logs", "⚡ Telemetry & Latency Specs"])

    with t1:
        st.subheader("Immutable System Audit Trail")
        if IS_API_CONNECTED:
            logs = requests.get(f"{API_BASE_URL}/audit-logs").json()
        elif HAS_BACKEND_MODULES:
            db = SessionLocal()
            try:
                logs = [l.to_dict() for l in AuditService.get_recent_logs(db)]
            finally:
                db.close()
        else:
            logs = []

        if logs:
            df_logs = pd.DataFrame(logs)
            st.dataframe(
                df_logs[["timestamp", "event_type", "entity_type", "entity_id", "message"]],
                use_container_width=True
            )
        else:
            st.info("No audit logs available.")

    with t2:
        st.subheader("System Observability & Latency Rules")
        st.markdown("""
        - **Request Latency Middleware:** FastAPI middleware computes process time per API request in `ms` and attaches `X-Process-Time` response header.
        - **Idempotency Guarantee:** Duplicate webhooks matching existing `event_id` are caught before DB lock to avoid processing overhead.
        - **Atomicity:** All state updates wrapped in isolated SQLAlchemy session transactions.
        """)
