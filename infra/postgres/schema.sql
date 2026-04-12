CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS products (
  id BIGSERIAL PRIMARY KEY,
  canonical_key TEXT NOT NULL UNIQUE,
  retailer TEXT NOT NULL CHECK (retailer IN ('amazon', 'flipkart')),
  title TEXT NOT NULL,
  product_url TEXT NOT NULL,
  currency_code CHAR(3) NOT NULL DEFAULT 'INR',
  current_price NUMERIC(12, 2),
  image_url TEXT,
  normalized_brand TEXT,
  normalized_model TEXT,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  last_scraped_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_products_retailer_model
  ON products (retailer, normalized_model);

CREATE INDEX IF NOT EXISTS idx_products_last_scraped_at
  ON products (last_scraped_at DESC);

CREATE TABLE IF NOT EXISTS price_history (
  id BIGSERIAL NOT NULL,
  product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  retailer TEXT NOT NULL CHECK (retailer IN ('amazon', 'flipkart')),
  offer_price NUMERIC(12, 2) NOT NULL,
  mrp_price NUMERIC(12, 2),
  availability TEXT,
  seller_name TEXT,
  raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  scraped_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (id, scraped_at)
) PARTITION BY RANGE (scraped_at);

CREATE TABLE IF NOT EXISTS price_history_2026
  PARTITION OF price_history
  FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');

CREATE INDEX IF NOT EXISTS idx_price_history_product_scraped
  ON price_history_2026 (product_id, scraped_at DESC);

CREATE INDEX IF NOT EXISTS idx_price_history_scraped
  ON price_history_2026 (scraped_at DESC);

CREATE INDEX IF NOT EXISTS idx_price_history_raw_payload
  ON price_history_2026 USING GIN (raw_payload);

CREATE TABLE IF NOT EXISTS user_alerts (
  id BIGSERIAL PRIMARY KEY,
  user_id TEXT NOT NULL,
  product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  target_price NUMERIC(12, 2) NOT NULL CHECK (target_price > 0),
  channel TEXT NOT NULL CHECK (channel IN ('push', 'email', 'whatsapp')),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  last_notified_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (user_id, product_id, channel)
);

CREATE INDEX IF NOT EXISTS idx_user_alerts_active_lookup
  ON user_alerts (is_active, product_id, target_price);
