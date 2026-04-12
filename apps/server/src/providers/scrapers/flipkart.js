const { normalizeProductIdentity, normalizeText } = require("../../../../packages/shared/src");
const { createBrowserSession } = require("./browser");

async function scrapeFlipkartProduct(url) {
  const session = await createBrowserSession();

  try {
    const { page } = session;
    await page.goto(url, { waitUntil: "domcontentloaded" });
    await page.waitForLoadState("networkidle").catch(() => null);
    await dismissLoginModal(page);
    await page.waitForSelector("span.B_NuCI, h1", { state: "visible" });

    const data = await page.evaluate(() => {
      const findText = (selectors) => {
        for (const selector of selectors) {
          const element = document.querySelector(selector);
          if (element?.textContent?.trim()) {
            return element.textContent.trim();
          }
        }
        return null;
      };

      const findAttr = (selectors, attr) => {
        for (const selector of selectors) {
          const element = document.querySelector(selector);
          const value = element?.getAttribute?.(attr);
          if (value?.trim()) {
            return value.trim();
          }
        }
        return null;
      };

      return {
        title: findText(["span.B_NuCI", "h1"]),
        offerPrice: findText(["div.Nx9bqj.CxhGGd", "div.Nx9bqj", "[class*='Nx9bqj']"]),
        mrpPrice: findText(["div.yRaY8j.A6+E6v", "div._3I9_wc"]),
        availability: findText(["button._2KpZ6l._2U9uOA._3v1-ww", "div._16FRp0"]),
        imageUrl: findAttr(["img._396cs4", "img._53J4C-"], "src"),
        sellerName: findText(["#sellerName span", "div.XQDdHH"])
      };
    });

    return formatScrapePayload("flipkart", url, data);
  } finally {
    await session.close();
  }
}

async function dismissLoginModal(page) {
  const closeButton = page.locator("button._2KpZ6l._2doB4z");
  if (await closeButton.count()) {
    await closeButton.first().click().catch(() => null);
  }
}

function formatScrapePayload(retailer, url, data) {
  const normalized = normalizeProductIdentity({
    retailer,
    title: data.title
  });

  return {
    retailer,
    productUrl: url,
    title: normalized.title,
    canonicalKey: normalized.canonicalKey,
    normalizedBrand: normalized.normalizedBrand,
    normalizedModel: normalized.normalizedModel,
    currencyCode: "INR",
    imageUrl: data.imageUrl || null,
    sellerName: normalizeText(data.sellerName || ""),
    availability: normalizeText(data.availability || ""),
    offerPrice: toAmount(data.offerPrice),
    mrpPrice: toAmount(data.mrpPrice),
    scrapedAt: new Date().toISOString(),
    rawPayload: data
  };
}

function toAmount(value) {
  const digits = String(value || "").replace(/[^\d]/g, "");
  return digits ? Number(digits) : null;
}

module.exports = { scrapeFlipkartProduct };
