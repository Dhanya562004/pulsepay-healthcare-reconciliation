/**
 * Server-only API client for communication with the PulsePay FastAPI backend.
 * The browser NEVER executes this code or sees the PULSEPAY_API_KEY.
 */

export interface PaymentItem {
  id: string;
  invoice_id: string;
  amount: number;
  status: "INITIATED" | "SUCCESS" | "FAILED" | string;
  provider: string;
  external_reference_id: string;
  failure_reason?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PaginationInfo {
  limit: number;
  offset: number;
  total: number;
  hasMore: boolean;
}

export interface PaginatedPaymentsResponse {
  data: PaymentItem[];
  pagination: PaginationInfo;
}

export interface WebhookEventItem {
  id: string;
  event_id: string;
  payment_id?: string | null;
  status: string;
  processing_status: string;
  payload?: string | null;
  processed_at?: string | null;
}

export interface PaymentDetail extends PaymentItem {
  webhook_event_statuses: string[];
  webhook_events: WebhookEventItem[];
}

function getBackendConfig() {
  const baseUrl = process.env.PULSEPAY_API_URL || "http://localhost:8000";
  const apiKey = process.env.PULSEPAY_API_KEY || "";
  return { baseUrl, apiKey };
}

/**
 * Fetch paginated list of payments with optional status filtering.
 */
export async function getPaymentsList(params: {
  page: number;
  limit?: number;
  status?: string;
}): Promise<PaginatedPaymentsResponse> {
  const { baseUrl, apiKey } = getBackendConfig();
  const limit = params.limit || 10;
  const offset = Math.max(0, (params.page - 1) * limit);

  const query = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString(),
  });

  if (params.status && params.status !== "ALL") {
    query.set("status", params.status);
  }

  const url = `${baseUrl}/payments?${query.toString()}`;

  // Caching strategy: The payments list uses Incremental Static Regeneration (ISR) / fetch revalidation
  // (revalidate: 30 seconds) because payments aggregate at volume and sub-minute freshness is sufficient
  // for listing and pagination, reducing backend load and improving Time to First Byte (TTFB).
  const response = await fetch(url, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      ...(apiKey ? { "X-Api-Key": apiKey } : {}),
    },
    next: {
      revalidate: 30,
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to fetch payments: ${response.status} ${response.statusText} - ${errorText}`);
  }

  return response.json();
}

/**
 * Fetch detailed record for a specific payment, including associated webhook events.
 */
export async function getPaymentDetail(id: string): Promise<PaymentDetail | null> {
  const { baseUrl, apiKey } = getBackendConfig();
  const url = `${baseUrl}/payments/${encodeURIComponent(id)}`;

  // Caching strategy: The payment detail page uses `cache: 'no-store'` (dynamic fetching)
  // because users inspecting a specific transaction need immediate, real-time reflection
  // of incoming webhook events and state transitions (e.g. INITIATED -> SUCCESS / FAILED).
  const response = await fetch(url, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      ...(apiKey ? { "X-Api-Key": apiKey } : {}),
    },
    cache: "no-store",
  });

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to fetch payment detail: ${response.status} ${response.statusText} - ${errorText}`);
  }

  return response.json();
}
