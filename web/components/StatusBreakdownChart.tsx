"use client";

import React from "react";
import { PaymentItem } from "@/lib/api";
import { formatCurrency } from "@/lib/format";

interface StatusBreakdownChartProps {
  payments: PaymentItem[];
}

export default function StatusBreakdownChart({ payments }: StatusBreakdownChartProps) {
  const counts = {
    SUCCESS: 0,
    FAILED: 0,
    INITIATED: 0,
    OTHER: 0,
  };

  let totalAmount = 0;

  for (const p of payments) {
    totalAmount += p.amount || 0;
    const st = (p.status || "").toUpperCase();
    if (st === "SUCCESS") counts.SUCCESS++;
    else if (st === "FAILED") counts.FAILED++;
    else if (st === "INITIATED") counts.INITIATED++;
    else counts.OTHER++;
  }

  const totalPayments = payments.length;

  const successPercent = totalPayments ? Math.round((counts.SUCCESS / totalPayments) * 100) : 0;
  const failedPercent = totalPayments ? Math.round((counts.FAILED / totalPayments) * 100) : 0;
  const initiatedPercent = totalPayments ? Math.round((counts.INITIATED / totalPayments) * 100) : 0;

  return (
    <section
      aria-label="Payment Status Breakdown on Current Page"
      className="mb-6 rounded-xl border border-slate-700/60 bg-slate-900/60 p-5 backdrop-blur-md shadow-lg"
    >
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
        <div>
          <h2 className="text-lg font-semibold text-slate-100">Status Distribution (Page Snapshot)</h2>
          <p className="text-xs text-slate-400">
            Breakdown across {totalPayments} payments on this page (Total volume: {formatCurrency(totalAmount)})
          </p>
        </div>
        <div className="flex flex-wrap gap-2 text-xs">
          <span className="inline-flex items-center gap-1.5 rounded-md bg-emerald-950/60 px-2.5 py-1 text-emerald-300 border border-emerald-800/50">
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
            Success: {counts.SUCCESS} ({successPercent}%)
          </span>
          <span className="inline-flex items-center gap-1.5 rounded-md bg-rose-950/60 px-2.5 py-1 text-rose-300 border border-rose-800/50">
            <span className="h-2 w-2 rounded-full bg-rose-400" />
            Failed: {counts.FAILED} ({failedPercent}%)
          </span>
          <span className="inline-flex items-center gap-1.5 rounded-md bg-amber-950/60 px-2.5 py-1 text-amber-300 border border-amber-800/50">
            <span className="h-2 w-2 rounded-full bg-amber-400" />
            Initiated: {counts.INITIATED} ({initiatedPercent}%)
          </span>
        </div>
      </div>

      {/* Visual Percentage Distribution Bar */}
      <div
        role="progressbar"
        aria-valuenow={successPercent}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Success rate: ${successPercent} percent`}
        className="h-3 w-full rounded-full bg-slate-800 overflow-hidden flex"
      >
        <div
          style={{ width: `${successPercent}%` }}
          className="bg-emerald-500 transition-all duration-500"
          title={`Success: ${successPercent}%`}
        />
        <div
          style={{ width: `${failedPercent}%` }}
          className="bg-rose-500 transition-all duration-500"
          title={`Failed: ${failedPercent}%`}
        />
        <div
          style={{ width: `${initiatedPercent}%` }}
          className="bg-amber-500 transition-all duration-500"
          title={`Initiated: ${initiatedPercent}%`}
        />
      </div>
    </section>
  );
}
