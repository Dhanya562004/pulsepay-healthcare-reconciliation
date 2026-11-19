"use client";

import React from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ALLOWED_STATUSES, PaymentStatusFilter } from "@/lib/search-params";

interface StatusFilterProps {
  currentStatus: PaymentStatusFilter;
}

export default function StatusFilter({ currentStatus }: StatusFilterProps) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const handleStatusChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newStatus = e.target.value;
    const params = new URLSearchParams(searchParams.toString());
    params.set("page", "1"); // Reset to page 1 on filter change
    if (newStatus === "ALL") {
      params.delete("status");
    } else {
      params.set("status", newStatus);
    }
    router.push(`/payments?${params.toString()}`);
  };

  return (
    <div className="flex items-center gap-3">
      <label
        htmlFor="status-filter"
        className="text-sm font-medium text-slate-300 whitespace-nowrap"
      >
        Filter by Status:
      </label>
      <select
        id="status-filter"
        name="status"
        value={currentStatus}
        onChange={handleStatusChange}
        className="rounded-lg border border-slate-700 bg-slate-800/90 px-3.5 py-2 text-sm text-slate-200 shadow-sm transition-colors focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-500/50"
      >
        {ALLOWED_STATUSES.map((status) => (
          <option key={status} value={status}>
            {status === "ALL" ? "All Statuses" : status}
          </option>
        ))}
      </select>
    </div>
  );
}
