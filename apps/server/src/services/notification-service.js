const { env } = require("../config/env");
const { logger } = require("../config/logger");

async function sendPriceDropNotification(alert) {
  const payload = {
    userId: alert.user_id,
    productId: alert.product_id,
    retailer: alert.retailer,
    title: alert.title,
    productUrl: alert.product_url,
    currentPrice: Number(alert.current_price),
    targetPrice: Number(alert.target_price),
    currencyCode: alert.currency_code,
    channel: alert.channel
  };

  if (!env.PRICE_ALERT_WEBHOOK_URL) {
    logger.info("Price alert triggered without webhook configured", payload);
    return { delivered: false, reason: "webhook_not_configured" };
  }

  const response = await fetch(env.PRICE_ALERT_WEBHOOK_URL, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(`Notification webhook failed with status ${response.status}`);
  }

  return { delivered: true };
}

module.exports = { sendPriceDropNotification };
