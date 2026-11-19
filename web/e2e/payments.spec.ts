import { test, expect } from "@playwright/test";

const TEST_API_KEY = "test-playwright-secret-key-xyz";
const DETAIL_PAYMENT_ID = "11111111-1111-1111-1111-111111111111";
const XSS_PAYMENT_ID = "22222222-2222-2222-2222-222222222222";

test.describe("PulsePay E2E Test Suite", () => {
  test("the list page renders rows and pagination controls", async ({ page }) => {
    await page.goto("/payments");

    // Table is visible
    const table = page.locator("table");
    await expect(table).toBeVisible();

    // 10 payment rows rendered on page 1 (out of 15 total)
    const rows = page.locator("tbody tr");
    await expect(rows).toHaveCount(10);

    // Pagination controls are visible
    const nav = page.locator('nav[aria-label="Payments pagination"]');
    await expect(nav).toBeVisible();
    await expect(nav).toContainText("Showing Page 1 of 2");

    // Previous button disabled on page 1
    const prevButton = page.getByText("← Previous");
    await expect(prevButton).toHaveAttribute("aria-disabled", "true");

    // Next link is active
    const nextLink = page.getByRole("link", { name: "Go to next page" });
    await expect(nextLink).toBeVisible();
    await expect(nextLink).toHaveAttribute("href", "/payments?page=2");
  });

  test("clicking Next changes the URL and the rows", async ({ page }) => {
    await page.goto("/payments");

    // Capture first payment link href on page 1
    const firstRowLinkPage1 = await page.locator("tbody tr td a").first().getAttribute("href");
    expect(firstRowLinkPage1).toBeTruthy();

    // Click Next link
    const nextLink = page.getByRole("link", { name: "Go to next page" });
    await nextLink.click();

    // URL changes to page 2
    await expect(page).toHaveURL(/.*[?&]page=2/);

    // Pagination updates to Page 2 of 2
    const nav = page.locator('nav[aria-label="Payments pagination"]');
    await expect(nav).toContainText("Showing Page 2 of 2");

    // Rows update: page 2 has the remaining 5 payments
    const rows = page.locator("tbody tr");
    await expect(rows).toHaveCount(5);

    // Verify the rows are different from page 1
    const firstRowLinkPage2 = await page.locator("tbody tr td a").first().getAttribute("href");
    expect(firstRowLinkPage2).toBeTruthy();
    expect(firstRowLinkPage1).not.toBe(firstRowLinkPage2);

    // On page 2, Next is disabled and Previous is an active link
    const nextButton = page.getByText("Next →");
    await expect(nextButton).toHaveAttribute("aria-disabled", "true");

    const prevLink = page.getByRole("link", { name: "Go to previous page" });
    await expect(prevLink).toBeVisible();
  });

  test("the status filter narrows the list", async ({ page }) => {
    await page.goto("/payments");

    // Filter by FAILED status
    const filterSelect = page.locator("#status-filter");
    await filterSelect.selectOption("FAILED");

    // URL updates with status=FAILED
    await expect(page).toHaveURL(/.*status=FAILED/);

    // All rows in table display Failed status
    const rows = page.locator("tbody tr");
    const rowCount = await rows.count();
    expect(rowCount).toBeGreaterThan(0);

    const failedBadges = page.locator("tbody tr", { hasText: "Failed" });
    await expect(failedBadges).toHaveCount(rowCount);
  });

  test("the detail page shows the payment fields and the webhook timeline", async ({ page }) => {
    await page.goto(`/payments/${DETAIL_PAYMENT_ID}`);

    // Main header and status
    await expect(page.getByRole("heading", { name: "Payment Details" })).toBeVisible();
    await expect(page.getByText("$1,250.00")).toBeVisible();
    await expect(page.locator("main").getByText("Success").first()).toBeVisible();

    // Transaction IDs
    await expect(page.getByText(DETAIL_PAYMENT_ID)).toBeVisible();
    await expect(page.getByText("aaaa1111-1111-1111-1111-111111111111")).toBeVisible();
    await expect(page.getByText("tx_stripe_detail_001")).toBeVisible();

    // Provider (exact match to distinguish from transaction reference containing stripe)
    await expect(page.getByText("stripe", { exact: true })).toBeVisible();

    // Webhook timeline section
    await expect(page.getByRole("heading", { name: "Webhook Event Timeline" })).toBeVisible();
    await expect(page.getByText("PROCESSED", { exact: true })).toBeVisible();
    await expect(page.getByText("DUPLICATE_IGNORED", { exact: true })).toBeVisible();
    await expect(page.getByText("DELAYED_IGNORED", { exact: true })).toBeVisible();
  });

  test("an unknown payment id shows the not-found page", async ({ page }) => {
    const unknownId = "00000000-0000-0000-0000-000000000000";
    await page.goto(`/payments/${unknownId}`);

    await expect(page.getByRole("heading", { name: "Payment Not Found" })).toBeVisible();
    await expect(page.getByText("The requested payment ID does not exist")).toBeVisible();

    const backLink = page.getByRole("link", { name: "← Back to Payments List" });
    await expect(backLink).toBeVisible();
    await expect(backLink).toHaveAttribute("href", "/payments");
  });

  test("a seeded payment whose text contains <script>alert(1)</script> renders as plain text and no script runs", async ({ page }) => {
    let alertTriggered = false;
    page.on("dialog", async (dialog) => {
      alertTriggered = true;
      await dialog.dismiss();
    });

    // Visit payments list where the XSS payment is rendered
    await page.goto("/payments");
    expect(alertTriggered).toBe(false);

    // Visit payment detail page for the XSS payment
    await page.goto(`/payments/${XSS_PAYMENT_ID}`);
    expect(alertTriggered).toBe(false);

    // Assert that the raw probe string renders as plain text in the DOM
    const xssProbeText = page.getByText("<script>alert(1)</script>");
    await expect(xssProbeText.first()).toBeVisible();

    // Assert that the probe string is rendered inside safe content elements (not as executable <script> tags)
    const elementsWithProbe = page.locator("span, td, dd", { hasText: "<script>alert(1)</script>" });
    const count = await elementsWithProbe.count();
    expect(count).toBeGreaterThan(0);

    // Verify no executable <script> tag with alert(1) was injected into the DOM
    const maliciousExecutableScript = await page.evaluate(() => {
      return Array.from(document.querySelectorAll("script")).some(
        (s) => s.textContent?.trim() === "alert(1)"
      );
    });
    expect(maliciousExecutableScript).toBe(false);
  });

  test("the API key never appears in the page HTML or in any request the browser makes", async ({ page }) => {
    const browserRequests: { url: string; headers: string; body?: string | null }[] = [];

    // Capture every request sent from the browser
    page.on("request", (req) => {
      browserRequests.push({
        url: req.url(),
        headers: JSON.stringify(req.headers()),
        body: req.postData(),
      });
    });

    // Navigate across pages
    await page.goto("/payments");
    await page.goto(`/payments/${DETAIL_PAYMENT_ID}`);

    // Verify browser network requests NEVER contain the test API key
    for (const req of browserRequests) {
      expect(req.url).not.toContain(TEST_API_KEY);
      expect(req.headers).not.toContain(TEST_API_KEY);
      if (req.body) {
        expect(req.body).not.toContain(TEST_API_KEY);
      }
    }

    // Verify HTML source code delivered to browser NEVER contains the test API key
    const pageContent = await page.content();
    expect(pageContent).not.toContain(TEST_API_KEY);
  });
});
