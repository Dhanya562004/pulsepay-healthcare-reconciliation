import { z } from "zod";

export const ALLOWED_STATUSES = ["ALL", "INITIATED", "SUCCESS", "FAILED"] as const;
export type PaymentStatusFilter = (typeof ALLOWED_STATUSES)[number];

export const PaymentSearchParamsSchema = z.object({
  page: z
    .coerce
    .number()
    .int()
    .positive()
    .default(1)
    .catch(1),
  status: z
    .enum(ALLOWED_STATUSES)
    .default("ALL")
    .catch("ALL"),
});

export type ValidatedPaymentParams = {
  page: number;
  status: PaymentStatusFilter;
};

/**
 * Safely parse and sanitize searchParams for the payments page.
 * Invalid or malicious inputs cleanly fall back to safe defaults (page 1, status ALL).
 */
export function parsePaymentSearchParams(
  rawParams?: Record<string, string | string[] | undefined>
): ValidatedPaymentParams {
  if (!rawParams) {
    return { page: 1, status: "ALL" };
  }

  const rawPage = Array.isArray(rawParams.page) ? rawParams.page[0] : rawParams.page;
  const rawStatus = Array.isArray(rawParams.status) ? rawParams.status[0] : rawParams.status;

  const normalizedStatus = typeof rawStatus === "string" ? rawStatus.toUpperCase() : undefined;

  const parsed = PaymentSearchParamsSchema.safeParse({
    page: rawPage,
    status: normalizedStatus,
  });

  if (!parsed.success) {
    return { page: 1, status: "ALL" };
  }

  return parsed.data;
}
