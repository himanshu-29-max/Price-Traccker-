const { normalizeProductIdentity, normalizeText } = require("../../../../packages/shared/src");
const { createBrowserSession } = require("./browser");

async function scrapeAmazonProduct(url) {
  const session = await createBrowserSession();

  try {
    const { page } = session;
    await page.goto(url, { waitUntil: "domcontentloaded" });
    await page.waitForLoadState("networkidle").catch(() => null);
    await page.waitForSelector("#productTitle, #title", { state: "visible" });

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
        title: findText(["#productTitle", "#title span"]),
        offerPrice:
          findText([
            "#corePriceDisplay_desktop_feature_div .a-price .a-offscreen",
            "#priceblock_dealprice",
            "#priceblock_ourprice",
            ".a-price.aok-align-center .a-offscreen"
          ]) || findAttr([".a-price .a-offscreen"], "textContent"),
        mrpPrice: findText([
          ".basisPrice .a-offscreen",
          ".a-price.a-text-price .a-offscreen",
          "#listPrice"
        ]),
        availability: findText(["#availability span", "#outOfStock"]),
        imageUrl: findAttr(["#landingImage", "#imgTagWrapperId img"], "src"),
        sellerName: findText(["#sellerProfileTriggerId", "#merchant-info"])
      };
    });

    return formatScrapePayload("amazon", url, data);
  } finally {
    await session.close();
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

module.exports = { scrapeAmazonProduct };
