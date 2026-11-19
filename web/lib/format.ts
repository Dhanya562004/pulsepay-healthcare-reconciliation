/**
 * Formatting utilities for PulsePay amounts, dates, and payment metadata.
 */

/**
 * Format a numeric amount as currency string (e.g. $1,250.00).
 */
export function formatCurrency(amount: number | null | undefined, currency: string = "USD"): string {
  if (amount === null || amount === undefined || isNaN(amount)) {
    return "$0.00";
  }

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

/**
 * Format an ISO timestamp string into a localized human-readable date and time.
 * Returns "—" if the date is invalid or missing.
 */
export function formatDateTime(isoString: string | null | undefined): string {
  if (!isoString) {
    return "—";
  }

  const date = new Date(isoString);
  if (isNaN(date.getTime())) {
    return "—";
  }

  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
    hour12: true,
    timeZone: "UTC",
  }).format(date) + " UTC";
}

/**
 * Capitalizes status strings for clean display (e.g. "SUCCESS" -> "Success").
 */
export function formatStatus(status: string | null | undefined): string {
  if (!status) return "Unknown";
  return status.charAt(0).toUpperCase() + status.slice(1).toLowerCase();
}
