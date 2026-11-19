import React from "react";

export default function PaymentsLoading() {
  return (
    <div className="space-y-6" aria-busy="true" aria-live="polite">
      {/* Header Skeleton */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="space-y-2">
          <div className="h-8 w-48 rounded-lg bg-slate-800 animate-pulse" />
          <div className="h-4 w-72 rounded bg-slate-800/60 animate-pulse" />
        </div>
        <div className="h-10 w-44 rounded-lg bg-slate-800 animate-pulse" />
      </div>

      {/* Breakdown Chart Skeleton */}
      <div className="h-28 rounded-xl border border-slate-800 bg-slate-900/50 p-5 animate-pulse" />

      {/* Table Skeleton */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 shadow-sm">
        <div className="space-y-3">
          <div className="h-10 w-full rounded-md bg-slate-800/80 animate-pulse" />
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-14 w-full rounded-md bg-slate-800/40 animate-pulse" />
          ))}
        </div>
      </div>
    </div>
  );
}
