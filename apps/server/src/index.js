const { createApp } = require("./app");
const { env } = require("./config/env");
const { logger } = require("./config/logger");

const app = createApp();

app.listen(env.PORT, () => {
  logger.info("HTTP server started", {
    port: env.PORT,
    environment: env.NODE_ENV
  });
});
