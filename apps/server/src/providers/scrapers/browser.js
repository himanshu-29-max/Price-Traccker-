const { chromium, devices } = require("playwright");
const { env } = require("../../config/env");

const desktopProfile = devices["Desktop Chrome"];

async function createBrowserSession() {
  const browser = await chromium.launch({
    headless: env.PLAYWRIGHT_HEADLESS,
    args: [
      "--disable-blink-features=AutomationControlled",
      "--disable-dev-shm-usage",
      "--no-sandbox"
    ]
  });

  const context = await browser.newContext({
    ...desktopProfile,
    locale: "en-IN",
    timezoneId: "Asia/Kolkata",
    viewport: { width: 1440, height: 1400 },
    userAgent:
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
  });

  await context.setExtraHTTPHeaders({
    "accept-language": "en-IN,en;q=0.9",
    dnt: "1",
    upgrade-insecure-requests: "1"
  });

  const page = await context.newPage();
  page.setDefaultTimeout(env.SCRAPE_TIMEOUT_MS);

  await page.addInitScript(() => {
    Object.defineProperty(navigator, "webdriver", {
      get: () => false
    });
  });

  return {
    browser,
    context,
    page,
    async close() {
      await context.close();
      await browser.close();
    }
  };
}

module.exports = { createBrowserSession };
