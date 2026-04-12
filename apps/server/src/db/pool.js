const { Pool } = require("pg");
const { env } = require("../config/env");

const pool = new Pool({
  connectionString: env.DATABASE_URL,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 10000,
  application_name: "price-tracker-platform"
});

module.exports = { pool };
