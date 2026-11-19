import React from "react";
import Link from "next/link";
import { notFound } from "next/navigation";
import { getPaymentDetail } from "@/lib/api";
import { formatCurrency, formatDateTime } from "@/lib/format";
import StatusBadge from "@/components/StatusBadge";

interface PaymentDetailPageProps {
  params: {
    id: string;
  };
}

export default async function PaymentDetailPage({ params }: PaymentDetailPageProps) {
  const payment = await getPaymentDetail(params.id);

  if (!payment) {
    notFound();
  }

  const webhookStatuses = payment.webhook_event_statuses || [];
  const webhookEvents = payment.webhook_events || [];

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Navigation Breadcrumb */}
      <div>
        <Link
          href="/payments"
          className="inline-flex items-center gap-1.5 text-sm font-medium text-sky-400 hover:text-sky-300 hover:underline focus:outline-none focus:ring-2 focus:ring-sky-400 rounded px-1 py-0.5"
        >
          ← Back to Payments List
        </Link>
      </div>

      {/* Main Payment Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-white">Payment Details</h1>
            <StatusBadge status={payment.status} />
          </div>
          <p className="mt-1 font-mono text-xs text-slate-400 select-all">
            ID: {payment.id}
          </p>
        </div>
        <div className="text-right sm:text-right">
          <p className="text-xs uppercase tracking-wider text-slate-400 font-medium">Transaction Amount</p>
          <p className="text-3xl font-extrabold text-white mt-0.5">
            {formatCurrency(payment.amount)}
          </p>
        </div>
      </div>

      {/* Metadata Grid */}
      <section aria-labelledby="payment-info-heading" className="space-y-4">
        <h2 id="payment-info-heading" className="text-lg font-semibold text-slate-200">
          Payment Information
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-sm space-y-3">
            <div>
              <span className="block text-xs uppercase tracking-wider text-slate-400 font-medium">Invoice ID</span>
              <span className="font-mono text-sm text-slate-200 select-all">
                {payment.invoice_id || "—"}
              </span>
            </div>
            <div>
              <span className="block text-xs uppercase tracking-wider text-slate-400 font-medium">Gateway Provider</span>
              <span className="text-sm font-medium text-slate-200 capitalize">
                {payment.provider}
              </span>
            </div>
            <div>
              <span className="block text-xs uppercase tracking-wider text-slate-400 font-medium">External Reference ID</span>
              <span className="font-mono text-xs text-slate-300 select-all">
                {payment.external_reference_id || "—"}
              </span>
            </div>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-sm space-y-3">
            <div>
              <span className="block text-xs uppercase tracking-wider text-slate-400 font-medium">Created Time</span>
              <span className="text-sm text-slate-200">
                {formatDateTime(payment.created_at)}
              </span>
            </div>
            <div>
              <span className="block text-xs uppercase tracking-wider text-slate-400 font-medium">Last Updated</span>
              <span className="text-sm text-slate-200">
                {formatDateTime(payment.updated_at)}
              </span>
            </div>
            {payment.failure_reason && (
              <div>
                <span className="block text-xs uppercase tracking-wider text-rose-400 font-medium">Failure Reason</span>
                <span className="text-xs text-rose-300 bg-rose-950/40 border border-rose-900/60 rounded px-2 py-1 inline-block mt-0.5">
                  {payment.failure_reason}
                </span>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Webhook Events Timeline */}
      <section aria-labelledby="webhook-timeline-heading" className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 id="webhook-timeline-heading" className="text-lg font-semibold text-slate-200">
            Webhook Event Timeline
          </h2>
          <span className="text-xs text-slate-400">
            {webhookStatuses.length} event{webhookStatuses.length === 1 ? "" : "s"} recorded
          </span>
        </div>

        {webhookStatuses.length === 0 ? (
          <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-8 text-center text-slate-400 text-sm">
            No webhook events recorded for this payment transaction.
          </div>
        ) : (
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 shadow-sm">
            <ol className="relative border-l border-slate-700 ml-3 space-y-6">
              {webhookEvents.length > 0 ? (
                webhookEvents.map((evt, index) => (
                  <li key={evt.id || index} className="ml-6">
                    <span className="absolute -left-2.5 flex h-5 w-5 items-center justify-center rounded-full bg-slate-800 ring-4 ring-slate-900 border border-slate-600 text-xs">
                      ⚡
                    </span>
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1">
                      <span className="text-sm font-semibold text-slate-200">
                        Event: <code className="font-mono text-xs text-sky-400">{evt.event_id}</code>
                      </span>
                      <time className="text-xs text-slate-400">
                        {formatDateTime(evt.processed_at)}
                      </time>
                    </div>

                    <div className="mt-2 flex flex-wrap items-center gap-2">
                      <span className="text-xs text-slate-400">Processing Decision:</span>
                      <span className="rounded bg-slate-800 px-2 py-0.5 text-xs font-mono font-medium text-emerald-400 border border-slate-700">
                        {evt.processing_status}
                      </span>
                      <span className="text-xs text-slate-400">Gateway Status:</span>
                      <StatusBadge status={evt.status} />
                    </div>

                    {evt.payload && (
                      <details className="mt-3 group">
                        <summary className="text-xs text-slate-400 hover:text-slate-200 cursor-pointer font-medium focus:outline-none focus:ring-1 focus:ring-sky-400 rounded px-1 py-0.5">
                          Inspect Payload JSON
                        </summary>
                        <pre className="mt-2 rounded-lg bg-slate-950 p-3 text-xs font-mono text-slate-300 overflow-x-auto border border-slate-800">
                          {evt.payload}
                        </pre>
                      </details>
                    )}
                  </li>
                ))
              ) : (
                webhookStatuses.map((st, index) => (
                  <li key={index} className="ml-6">
                    <span className="absolute -left-2.5 flex h-5 w-5 items-center justify-center rounded-full bg-slate-800 ring-4 ring-slate-900 border border-slate-600 text-xs">
                      ⚡
                    </span>
                    <p className="text-sm font-semibold text-slate-200">
                      Processing Status: <span className="font-mono text-emerald-400">{st}</span>
                    </p>
                  </li>
                ))
              )}
            </ol>
          </div>
        )}
      </section>
    </div>
  );
}
