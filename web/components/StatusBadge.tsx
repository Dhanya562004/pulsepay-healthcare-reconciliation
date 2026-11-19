import React from "react";
import { formatStatus } from "@/lib/format";

interface StatusBadgeProps {
  status: string;
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  const normalized = (status || "").toUpperCase();

  let colorClasses = "bg-slate-800 text-slate-300 border-slate-700";
  let dotColor = "bg-slate-400";

  if (normalized === "SUCCESS" || normalized === "PAID") {
    colorClasses = "bg-emerald-950/70 text-emerald-300 border-emerald-800/60";
    dotColor = "bg-emerald-400";
  } else if (normalized === "FAILED") {
    colorClasses = "bg-rose-950/70 text-rose-300 border-rose-800/60";
    dotColor = "bg-rose-400";
  } else if (normalized === "INITIATED" || normalized === "PENDING") {
    colorClasses = "bg-amber-950/70 text-amber-300 border-amber-800/60";
    dotColor = "bg-amber-400";
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium tracking-wide ${colorClasses}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${dotColor}`} aria-hidden="true" />
      {formatStatus(status)}
    </span>
  );
}
