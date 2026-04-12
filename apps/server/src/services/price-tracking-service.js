const { toPriceChartResponse } = require("../../../../packages/shared/src");
const {
  findProductById,
  getPriceHistory,
  insertPriceHistory,
  listActiveAlertsForCheck,
  listRecentlyTrackedProducts,
  markAlertNotified,
  syncCurrentPrice,
  upsertProduct,
  withTransaction
} = require("../db/queries");
const { scrapeProduct } = require("../providers/scrapers");
const { sendPriceDropNotification } = require("./notification-service");

async function scrapeAndStoreProduct(url) {
  const scraped = await scrapeProduct(url);
  if (!scraped.offerPrice) {
    throw new Error(`Could not extract a price for ${url}`);
  }

  return withTransaction(async (client) => {
    const product = await upsertProduct(client, scraped);
    await insertPriceHistory(client, {
      productId: product.id,
      retailer: scraped.retailer,
      offerPrice: scraped.offerPrice,
      mrpPrice: scraped.mrpPrice,
      availability: scraped.availability,
      sellerName: scraped.sellerName,
      scrapedAt: scraped.scrapedAt,
      rawPayload: scraped.rawPayload
    });
    await syncCurrentPrice(client, product.id, scraped.offerPrice);

    return {
      ...product,
      current_price: scraped.offerPrice
    };
  });
}

async function fetchPriceHistoryChart(productId, rangeDays) {
  const product = await findProductById(productId);
  if (!product) {
    const error = new Error("Product not found");
    error.statusCode = 404;
    throw error;
  }

  const history = await getPriceHistory(productId, rangeDays);
  return toPriceChartResponse(product, history);
}

async function runPriceDropCheck(limit = 100) {
  const trackedProducts = await listRecentlyTrackedProducts(limit);
  for (const product of trackedProducts) {
    await scrapeAndStoreProduct(product.product_url);
  }

  const alerts = await listActiveAlertsForCheck();
  const results = [];

  for (const alert of alerts) {
    if (Number(alert.current_price) > Number(alert.target_price)) {
      continue;
    }

    await sendPriceDropNotification(alert);
    await markAlertNotified(alert.id);
    results.push({
      alertId: alert.id,
      productId: alert.product_id,
      currentPrice: Number(alert.current_price)
    });
  }

  return results;
}

module.exports = {
  fetchPriceHistoryChart,
  runPriceDropCheck,
  scrapeAndStoreProduct
};
