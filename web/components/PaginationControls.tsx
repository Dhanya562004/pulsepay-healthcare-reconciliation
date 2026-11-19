import React from "react";
import Link from "next/link";
import { PaymentStatusFilter } from "@/lib/search-params";

interface PaginationControlsProps {
  currentPage: number;
  totalItems: number;
  pageSize: number;
  hasMore: boolean;
  status: PaymentStatusFilter;
}

export default function PaginationControls({
  currentPage,
  totalItems,
  pageSize,
  hasMore,
  status,
}: PaginationControlsProps) {
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  const hasPrev = currentPage > 1;
  const hasNext = hasMore && currentPage < totalPages;

  function buildUrl(page: number) {
    const params = new URLSearchParams();
    params.set("page", page.toString());
    if (status !== "ALL") {
      params.set("status", status);
    }
    return `/payments?${params.toString()}`;
  }

  return (
    <nav
      aria-label="Payments pagination"
      className="mt-6 flex flex-col sm:flex-row items-center justify-between gap-4 border-t border-slate-800 pt-4"
    >
      <div className="text-sm text-slate-400">
        Showing Page <span className="font-semibold text-slate-200">{currentPage}</span> of{" "}
        <span className="font-semibold text-slate-200">{totalPages}</span>{" "}
        <span className="text-slate-500">({totalItems} total payments)</span>
      </div>

      <div className="flex items-center gap-3">
        {hasPrev ? (
          <Link
            href={buildUrl(currentPage - 1)}
            aria-label="Go to previous page"
            className="inline-flex items-center justify-center rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-medium text-slate-200 shadow-sm transition-all hover:bg-slate-700 hover:text-white focus:outline-none focus:ring-2 focus:ring-sky-500 focus:ring-offset-2 focus:ring-offset-slate-900"
          >
            ← Previous
          </Link>
        ) : (
          <span
            aria-disabled="true"
            className="inline-flex items-center justify-center rounded-lg border border-slate-800 bg-slate-900/40 px-4 py-2 text-sm font-medium text-slate-600 cursor-not-allowed select-none"
          >
            ← Previous
          </span>
        )}

        {hasNext ? (
          <Link
            href={buildUrl(currentPage + 1)}
            aria-label="Go to next page"
            className="inline-flex items-center justify-center rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-medium text-slate-200 shadow-sm transition-all hover:bg-slate-700 hover:text-white focus:outline-none focus:ring-2 focus:ring-sky-500 focus:ring-offset-2 focus:ring-offset-slate-900"
          >
            Next →
          </Link>
        ) : (
          <span
            aria-disabled="true"
            className="inline-flex items-center justify-center rounded-lg border border-slate-800 bg-slate-900/40 px-4 py-2 text-sm font-medium text-slate-600 cursor-not-allowed select-none"
          >
            Next →
          </span>
        )}
      </div>
    </nav>
  );
}
