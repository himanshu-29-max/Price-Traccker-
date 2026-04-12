const express = require("express");
const { healthRouter } = require("./routes/health");
const { productsRouter } = require("./routes/products");

const apiRouter = express.Router();

apiRouter.use("/health", healthRouter);
apiRouter.use("/products", productsRouter);

module.exports = { apiRouter };
