import { describe, it, expect } from "vitest";
import { formatCurrency, formatDateTime, formatStatus } from "./format";

describe("formatCurrency", () => {
  it("formats standard positive amounts correctly", () => {
    expect(formatCurrency(1250)).toBe("$1,250.00");
    expect(formatCurrency(45.5)).toBe("$45.50");
    expect(formatCurrency(1000000)).toBe("$1,000,000.00");
  });

  it("formats zero correctly", () => {
    expect(formatCurrency(0)).toBe("$0.00");
  });

  it("formats negative amounts correctly", () => {
    expect(formatCurrency(-50)).toBe("-$50.00");
  });

  it("handles null, undefined and NaN safely", () => {
    expect(formatCurrency(null)).toBe("$0.00");
    expect(formatCurrency(undefined)).toBe("$0.00");
    expect(formatCurrency(NaN)).toBe("$0.00");
  });

  it("supports other currencies when specified", () => {
    expect(formatCurrency(100, "EUR")).toMatch(/100\.00/);
  });
});

describe("formatDateTime", () => {
  it("formats valid UTC ISO dates accurately", () => {
    const formatted = formatDateTime("2025-05-10T14:30:00Z");
    expect(formatted).toContain("May 10, 2025");
    expect(formatted).toContain("2:30:00 PM UTC");
  });

  it("returns fallback for null, undefined, or empty string", () => {
    expect(formatDateTime(null)).toBe("—");
    expect(formatDateTime(undefined)).toBe("—");
    expect(formatDateTime("")).toBe("—");
  });

  it("returns fallback for invalid date strings", () => {
    expect(formatDateTime("not-a-date")).toBe("—");
  });
});

describe("formatStatus", () => {
  it("normalizes uppercase status strings", () => {
    expect(formatStatus("SUCCESS")).toBe("Success");
    expect(formatStatus("FAILED")).toBe("Failed");
    expect(formatStatus("INITIATED")).toBe("Initiated");
  });

  it("handles empty or null status", () => {
    expect(formatStatus(null)).toBe("Unknown");
    expect(formatStatus(undefined)).toBe("Unknown");
    expect(formatStatus("")).toBe("Unknown");
  });
});
