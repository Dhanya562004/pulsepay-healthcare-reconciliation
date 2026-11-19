import React from "react";
import Link from "next/link";

export default function PaymentNotFound() {
  return (
    <div
      role="status"
      className="mx-auto max-w-lg rounded-xl border border-slate-800 bg-slate-900/60 p-8 text-center text-slate-100 shadow-xl"
    >
      <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-slate-800 text-slate-300 text-2xl border border-slate-700">
        🔍
      </div>
      <h1 className="text-xl font-bold text-slate-100">Payment Not Found</h1>
      <p className="mt-2 text-sm text-slate-400">
        The requested payment ID does not exist or may have been removed.
      </p>

      <div className="mt-6">
        <Link
          href="/payments"
          className="inline-flex items-center gap-1.5 rounded-lg bg-sky-600 px-5 py-2.5 text-sm font-semibold text-white shadow hover:bg-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-400 focus:ring-offset-2 focus:ring-offset-slate-900 transition-colors"
        >
          ← Back to Payments List
        </Link>
      </div>
    </div>
  );
}
