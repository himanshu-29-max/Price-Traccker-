const { pool } = require("./pool");

async function withTransaction(executor) {
  const client = await pool.connect();
  try {
    await client.query("BEGIN");
    const result = await executor(client);
    await client.query("COMMIT");
    return result;
  } catch (error) {
    await client.query("ROLLBACK");
    throw error;
  } finally {
    client.release();
  }
}

async function upsertProduct(client, product) {
  const query = `
    INSERT INTO products (
      canonical_key,
      retailer,
      title,
      product_url,
      currency_code,
      image_url,
      normalized_brand,
      normalized_model
    )
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    ON CONFLICT (canonical_key)
    DO UPDATE SET
      retailer = EXCLUDED.retailer,
      title = EXCLUDED.title,
      product_url = EXCLUDED.product_url,
      currency_code = EXCLUDED.currency_code,
      image_url = EXCLUDED.image_url,
      normalized_brand = EXCLUDED.normalized_brand,
      normalized_model = EXCLUDED.normalized_model,
      updated_at = NOW()
    RETURNING *;
  `;

  const values = [
    product.canonicalKey,
    product.retailer,
    product.title,
    product.productUrl,
    product.currencyCode,
    product.imageUrl,
    product.normalizedBrand,
    product.normalizedModel
  ];

  const { rows } = await client.query(query, values);
  return rows[0];
}

async function insertPriceHistory(client, pricePoint) {
  const query = `
    INSERT INTO price_history (
      product_id,
      retailer,
      offer_price,
      mrp_price,
      availability,
      seller_name,
      scraped_at,
      raw_payload
    )
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    RETURNING *;
  `;

  const values = [
    pricePoint.productId,
    pricePoint.retailer,
    pricePoint.offerPrice,
    pricePoint.mrpPrice,
    pricePoint.availability,
    pricePoint.sellerName,
    pricePoint.scrapedAt,
    JSON.stringify(pricePoint.rawPayload || {})
  ];

  const { rows } = await client.query(query, values);
  return rows[0];
}

async function syncCurrentPrice(client, productId, price) {
  await client.query(
    `
      UPDATE products
      SET
        current_price = $2,
        last_scraped_at = NOW(),
        updated_at = NOW()
      WHERE id = $1;
    `,
    [productId, price]
  );
}

async function findProductById(productId) {
  const { rows } = await pool.query(
    `SELECT * FROM products WHERE id = $1 LIMIT 1;`,
    [productId]
  );
  return rows[0] || null;
}

async function findProductByCanonicalKey(canonicalKey) {
  const { rows } = await pool.query(
    `SELECT * FROM products WHERE canonical_key = $1 LIMIT 1;`,
    [canonicalKey]
  );
  return rows[0] || null;
}

async function findProductByUrl(productUrl) {
  const { rows } = await pool.query(
    `SELECT * FROM products WHERE product_url = $1 ORDER BY updated_at DESC LIMIT 1;`,
    [productUrl]
  );
  return rows[0] || null;
}

async function getPriceHistory(productId, rangeDays) {
  const { rows } = await pool.query(
    `
      SELECT
        product_id,
        offer_price,
        mrp_price,
        availability,
        seller_name,
        scraped_at
      FROM price_history
      WHERE product_id = $1
        AND scraped_at >= NOW() - ($2::text || ' days')::interval
      ORDER BY scraped_at ASC;
    `,
    [productId, rangeDays]
  );
  return rows;
}

async function upsertUserAlert({ userId, productId, targetPrice, channel = "push" }) {
  const { rows } = await pool.query(
    `
      INSERT INTO user_alerts (user_id, product_id, target_price, channel, is_active)
      VALUES ($1, $2, $3, $4, TRUE)
      ON CONFLICT (user_id, product_id, channel)
      DO UPDATE SET
        target_price = EXCLUDED.target_price,
        is_active = TRUE,
        updated_at = NOW()
      RETURNING *;
    `,
    [userId, productId, targetPrice, channel]
  );
  return rows[0];
}

async function listActiveAlertsForCheck() {
  const { rows } = await pool.query(`
    SELECT
      ua.id,
      ua.user_id,
      ua.product_id,
      ua.target_price,
      ua.channel,
      ua.last_notified_at,
      p.title,
      p.product_url,
      p.current_price,
      p.currency_code,
      p.retailer
    FROM user_alerts ua
    INNER JOIN products p ON p.id = ua.product_id
    WHERE ua.is_active = TRUE
      AND p.current_price IS NOT NULL;
  `);
  return rows;
}

async function markAlertNotified(alertId) {
  await pool.query(
    `UPDATE user_alerts SET last_notified_at = NOW(), updated_at = NOW() WHERE id = $1;`,
    [alertId]
  );
}

async function listRecentlyTrackedProducts(limit = 100) {
  const { rows } = await pool.query(
    `
      SELECT *
      FROM products
      WHERE is_active = TRUE
      ORDER BY last_scraped_at DESC NULLS LAST, updated_at DESC
      LIMIT $1;
    `,
    [limit]
  );
  return rows;
}

module.exports = {
  findProductByCanonicalKey,
  findProductById,
  findProductByUrl,
  getPriceHistory,
  insertPriceHistory,
  listActiveAlertsForCheck,
  listRecentlyTrackedProducts,
  markAlertNotified,
  syncCurrentPrice,
  upsertProduct,
  upsertUserAlert,
  withTransaction
};
