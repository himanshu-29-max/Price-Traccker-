const cors = require("cors");
const express = require("express");
const helmet = require("helmet");
const morgan = require("morgan");
const { apiRouter } = require("./api");
const { logger } = require("./config/logger");

function createApp() {
  const app = express();

  app.use(helmet());
  app.use(cors());
  app.use(express.json({ limit: "1mb" }));
  app.use(morgan("combined"));

  app.use("/api/v1", apiRouter);

  app.use((req, res) => {
    res.status(404).json({
      error: "Not Found"
    });
  });

  app.use((error, req, res, next) => {
    logger.error("Unhandled request error", {
      path: req.path,
      message: error.message,
      stack: error.stack
    });

    res.status(error.statusCode || 500).json({
      error: error.message || "Internal Server Error"
    });
  });

  return app;
}

module.exports = { createApp };
