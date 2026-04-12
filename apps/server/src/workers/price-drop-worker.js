const cron = require("node-cron");
const { env } = require("../config/env");
const { logger } = require("../config/logger");
const { runPriceDropCheck } = require("../services/price-tracking-service");

async function executePriceCheck() {
  logger.info("Starting hourly price-drop job");
  try {
    const results = await runPriceDropCheck();
    logger.info("Completed hourly price-drop job", {
      alertsTriggered: results.length
    });
  } catch (error) {
    logger.error("Price-drop job failed", {
      message: error.message,
      stack: error.stack
    });
  }
}

cron.schedule(env.PRICE_CHECK_CRON, executePriceCheck, {
  timezone: "Asia/Kolkata"
});

executePriceCheck();
