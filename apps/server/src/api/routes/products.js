const express = require("express");
const { z } = require("zod");
const { upsertUserAlert } = require("../../db/queries");
const {
  fetchPriceHistoryChart,
  scrapeAndStoreProduct
} = require("../../services/price-tracking-service");
const { asyncHandler } = require("../../utils/async-handler");

const router = express.Router();

const scrapeSchema = z.object({
  url: z.string().url()
});

const alertSchema = z.object({
  userId: z.string().min(1),
  targetPrice: z.coerce.number().positive(),
  channel: z.enum(["push", "email", "whatsapp"]).default("push")
});

router.post(
  "/scrape",
  asyncHandler(async (req, res) => {
    const body = scrapeSchema.parse(req.body);
    const product = await scrapeAndStoreProduct(body.url);
    res.status(201).json({
      data: product
    });
  })
);

router.get(
  "/:productId/history",
  asyncHandler(async (req, res) => {
    const productId = z.coerce.number().int().positive().parse(req.params.productId);
    const rangeDays = z.coerce.number().int().min(1).max(365).default(180).parse(req.query.rangeDays ?? 180);
    const payload = await fetchPriceHistoryChart(productId, rangeDays);
    res.json(payload);
  })
);

router.post(
  "/:productId/alerts",
  asyncHandler(async (req, res) => {
    const productId = z.coerce.number().int().positive().parse(req.params.productId);
    const body = alertSchema.parse(req.body);
    const alert = await upsertUserAlert({
      userId: body.userId,
      productId,
      targetPrice: body.targetPrice,
      channel: body.channel
    });
    res.status(201).json({ data: alert });
  })
);

module.exports = { productsRouter: router };
