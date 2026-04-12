const path = require("path");
const dotenv = require("dotenv");
const { z } = require("zod");

dotenv.config({ path: path.resolve(process.cwd(), ".env") });

const envSchema = z.object({
  NODE_ENV: z.enum(["development", "test", "production"]).default("development"),
  PORT: z.coerce.number().int().positive().default(4000),
  DATABASE_URL: z.string().min(1),
  SCRAPE_TIMEOUT_MS: z.coerce.number().int().positive().default(45000),
  PRICE_CHECK_CRON: z.string().min(1).default("0 * * * *"),
  PLAYWRIGHT_HEADLESS: z
    .string()
    .optional()
    .transform((value) => value !== "false"),
  PRICE_ALERT_WEBHOOK_URL: z.string().optional().default("")
});

const env = envSchema.parse(process.env);

module.exports = { env };
