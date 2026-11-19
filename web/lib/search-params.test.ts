import { describe, it, expect } from "vitest";
import { parsePaymentSearchParams } from "./search-params";

describe("parsePaymentSearchParams", () => {
  it("parses valid page and status correctly", () => {
    const result = parsePaymentSearchParams({ page: "3", status: "SUCCESS" });
    expect(result).toEqual({ page: 3, status: "SUCCESS" });
  });

  it("handles case-insensitivity in status", () => {
    const result = parsePaymentSearchParams({ page: "2", status: "failed" });
    expect(result).toEqual({ page: 2, status: "FAILED" });
  });

  it("falls back to default page 1 and status ALL when undefined or empty", () => {
    expect(parsePaymentSearchParams(undefined)).toEqual({ page: 1, status: "ALL" });
    expect(parsePaymentSearchParams({})).toEqual({ page: 1, status: "ALL" });
  });

  it("falls back to page 1 for zero or negative page values", () => {
    expect(parsePaymentSearchParams({ page: "0" })).toEqual({ page: 1, status: "ALL" });
    expect(parsePaymentSearchParams({ page: "-10" })).toEqual({ page: 1, status: "ALL" });
  });

  it("falls back to page 1 for non-numeric or malicious page values", () => {
    expect(parsePaymentSearchParams({ page: "abc" })).toEqual({ page: 1, status: "ALL" });
    expect(parsePaymentSearchParams({ page: "<script>" })).toEqual({ page: 1, status: "ALL" });
    expect(parsePaymentSearchParams({ page: "1.5" })).toEqual({ page: 1, status: "ALL" });
  });

  it("falls back to status ALL for unknown status values", () => {
    expect(parsePaymentSearchParams({ status: "UNKNOWN" })).toEqual({ page: 1, status: "ALL" });
    expect(parsePaymentSearchParams({ status: "random_text" })).toEqual({ page: 1, status: "ALL" });
  });

  it("handles array parameters cleanly (takes first element)", () => {
    expect(parsePaymentSearchParams({ page: ["4", "5"], status: ["INITIATED", "SUCCESS"] })).toEqual({
      page: 4,
      status: "INITIATED",
    });
  });
});
