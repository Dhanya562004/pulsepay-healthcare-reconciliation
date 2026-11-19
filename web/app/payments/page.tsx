import React from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import { getPaymentsList } from "@/lib/api";
import { parsePaymentSearchParams } from "@/lib/search-params";
import { formatCurrency, formatDateTime } from "@/lib/format";
import StatusFilter from "@/components/StatusFilter";
import StatusBadge from "@/components/StatusBadge";
import PaginationControls from "@/components/PaginationControls";

// Performance requirement: Lazy loading / code splitting with next/dynamic and a loading fallback
const StatusBreakdownChart = dynamic(() => import("@/components/StatusBreakdownChart"), {
  loading: () => (
    <div
      role="status"
      aria-label="Loading status breakdown chart"
      className="mb-6 h-28 rounded-xl border border-slate-800 bg-slate-900/50 p-5 animate-pulse flex items-center justify-center text-xs text-slate-500"
    >
      Loading status breakdown...
    </div>
  ),
});

interface PaymentsPageProps {
  searchParams?: Record<string, string | string[] | undefined>;
}

export default async function PaymentsPage({ searchParams }: PaymentsPageProps) {
  // Validate and sanitize search parameters using Zod with safe fallbacks
  const { page, status } = parsePaymentSearchParams(searchParams);

  // Fetch paginated payments list from the backend (server-only with revalidate: 30)
  const pageSize = 10;
  const result = await getPaymentsList({
    page,
    limit: pageSize,
    status: status === "ALL" ? undefined : status,
  });

  const payments = result.data || [];
  const pagination = result.pagination || {
    limit: pageSize,
    offset: 0,
    total: 0,
    hasMore: false,
  };

  return (
    <div className="space-y-6">
      {/* Top Header & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Healthcare Payments</h1>
          <p className="mt-1 text-sm text-slate-400">
            Monitor, audit, and inspect real-time healthcare billing transactions and gateway statuses.
          </p>
        </div>
        <div>
          <StatusFilter currentStatus={status} />
        </div>
      </div>

      {/* Lazy-loaded Status Breakdown Chart */}
      {payments.length > 0 && <StatusBreakdownChart payments={payments} />}

      {/* Main Payments Content: Semantic Table or Empty State */}
      {payments.length === 0 ? (
        <div
          role="status"
          className="rounded-xl border border-slate-800 bg-slate-900/50 p-12 text-center text-slate-300 shadow-sm"
        >
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-slate-800 text-slate-400 text-xl">
            📋
          </div>
          <h2 className="text-lg font-semibold text-slate-200">No payments found</h2>
          <p className="mt-1 text-sm text-slate-400 max-w-sm mx-auto">
            {status !== "ALL"
              ? `There are no transactions with status '${status}'. Try switching to 'All Statuses'.`
              : "No payment records exist in the system yet."}
          </p>
          {status !== "ALL" && (
            <div className="mt-5">
              <Link
                href="/payments"
                className="inline-flex items-center rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium text-white shadow hover:bg-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-400"
              >
                Clear Filter
              </Link>
            </div>
          )}
        </div>
      ) : (
        <div className="rounded-xl border border-slate-800/90 bg-slate-900/70 shadow-lg backdrop-blur-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300 border-collapse">
              <caption className="sr-only">
                Healthcare Payment Transactions List. Page {page} of {Math.ceil(pagination.total / pageSize)}.
              </caption>
              <thead className="bg-slate-950/70 border-b border-slate-800 text-xs uppercase tracking-wider text-slate-400 font-semibold">
                <tr>
                  <th scope="col" className="px-6 py-4">Payment ID</th>
                  <th scope="col" className="px-6 py-4">Invoice ID</th>
                  <th scope="col" className="px-6 py-4">Amount</th>
                  <th scope="col" className="px-6 py-4">Status</th>
                  <th scope="col" className="px-6 py-4">Gateway Provider</th>
                  <th scope="col" className="px-6 py-4">Created Time</th>
                  <th scope="col" className="px-6 py-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/70">
                {payments.map((payment) => (
                  <tr
                    key={payment.id}
                    className="hover:bg-slate-800/50 transition-colors focus-within:bg-slate-800/60"
                  >
                    <td className="px-6 py-4 font-mono text-xs text-sky-400">
                      <Link
                        href={`/payments/${payment.id}`}
                        className="hover:underline focus:outline-none focus:ring-2 focus:ring-sky-400 rounded px-1 py-0.5"
                        title={payment.id}
                      >
                        {payment.id.slice(0, 8)}...
                      </Link>
                    </td>
                    <td className="px-6 py-4 font-mono text-xs text-slate-400" title={payment.invoice_id}>
                      {payment.invoice_id ? `${payment.invoice_id.slice(0, 8)}...` : "—"}
                    </td>
                    <td className="px-6 py-4 font-semibold text-slate-100">
                      {formatCurrency(payment.amount)}
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={payment.status} />
                    </td>
                    <td className="px-6 py-4 text-xs capitalize text-slate-300">
                      {payment.provider}
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-400 whitespace-nowrap">
                      {formatDateTime(payment.created_at)}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link
                        href={`/payments/${payment.id}`}
                        className="inline-flex items-center text-xs font-medium text-sky-400 hover:text-sky-300 hover:underline focus:outline-none focus:ring-2 focus:ring-sky-400 rounded px-2 py-1"
                      >
                        View Details →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Server-Driven Pagination Controls */}
          <div className="px-6 pb-4">
            <PaginationControls
              currentPage={page}
              totalItems={pagination.total}
              pageSize={pageSize}
              hasMore={pagination.hasMore}
              status={status}
            />
          </div>
        </div>
      )}
    </div>
  );
}
