import { defineConfig, devices } from "@playwright/test";

const TEST_API_KEY = "test-playwright-secret-key-xyz";

export default defineConfig({
  testDir: "./e2e",
  timeout: 30 * 1000,
  expect: {
    timeout: 5000,
  },
  fullyParallel: false,
  retries: 0,
  workers: 1,
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:3000",
    trace: "off",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: [
    {
      command: "python scripts/start_test_backend.py",
      url: "http://127.0.0.1:8000/",
      reuseExistingServer: !process.env.CI,
      timeout: 30 * 1000,
      env: {
        API_KEY: TEST_API_KEY,
      },
    },
    {
      command: "npm run start -- -p 3000",
      url: "http://127.0.0.1:3000/payments",
      reuseExistingServer: !process.env.CI,
      timeout: 30 * 1000,
      env: {
        PULSEPAY_API_URL: "http://127.0.0.1:8000",
        PULSEPAY_API_KEY: TEST_API_KEY,
      },
    },
  ],
});
