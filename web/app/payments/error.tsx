"use client";

import React, { useEffect } from "react";
import Link from "next/link";

export default function PaymentsError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log client error to console
    console.error("Payments page error caught:", error);
  }, [error]);

  return (
    <div
      role="alert"
      className="rounded-xl border border-rose-800/60 bg-rose-950/30 p-8 text-center text-slate-100 shadow-xl"
    >
      <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-rose-900/50 text-rose-300 text-2xl border border-rose-700/50">
        ⚠️
      </div>
      <h2 className="text-xl font-bold text-rose-200">Failed to load payments</h2>
      <p className="mt-2 text-sm text-slate-300 max-w-md mx-auto">
        {error.message || "An unexpected error occurred while communicating with the backend."}
      </p>

      <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
        <button
          onClick={() => reset()}
          className="rounded-lg bg-sky-600 px-5 py-2.5 text-sm font-semibold text-white shadow hover:bg-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-400 focus:ring-offset-2 focus:ring-offset-slate-900 transition-colors"
        >
          Try again
        </button>
        <Link
          href="/payments"
          className="rounded-lg border border-slate-700 bg-slate-800 px-5 py-2.5 text-sm font-medium text-slate-200 shadow hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-sky-400 focus:ring-offset-2 focus:ring-offset-slate-900 transition-colors"
        >
          Reset filters
        </Link>
      </div>
    </div>
  );
}
