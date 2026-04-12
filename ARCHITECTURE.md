# Price Tracking Platform Backend

This repo now includes a production-oriented backend foundation for a BuyHatke-style platform.

## Layout

- `apps/server/`: Express API, scraper providers, workers, and database access.
- `packages/shared/`: shared logic and DTO formatters intended to be consumed by Next.js and React Native clients.
- `infra/postgres/schema.sql`: PostgreSQL schema optimized for high-volume price history.

## Implemented backend pieces

- Express.js API server
- Playwright scraper providers for Amazon and Flipkart
- PostgreSQL schema for `products`, `price_history`, and `user_alerts`
- Price history chart API
- Hourly price-drop worker
- Shared logic package for reusable identity normalization and chart DTO shaping

## Main endpoints

- `GET /api/v1/health`
- `POST /api/v1/products/scrape`
- `GET /api/v1/products/:productId/history?rangeDays=180`
- `POST /api/v1/products/:productId/alerts`

## Shared core strategy

The reusable logic lives in `packages/shared/src`:

- product identity normalization
- retailer constants
- chart API response shaping

That same package can be imported by:

- a Next.js web app for product pages and dashboards
- a React Native app for alerts, watchlists, and graphs

## Notes

- `price_history` is partitioned by `scraped_at` to scale into millions of price points.
- For real production rollout, create future yearly or monthly partitions automatically via migrations.
- The current notification implementation posts to a webhook if `PRICE_ALERT_WEBHOOK_URL` is set.
