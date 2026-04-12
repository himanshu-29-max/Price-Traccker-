const { scrapeAmazonProduct } = require("./amazon");
const { scrapeFlipkartProduct } = require("./flipkart");

function resolveRetailerFromUrl(url) {
  const host = new URL(url).hostname.toLowerCase();
  if (host.includes("amazon.")) {
    return "amazon";
  }
  if (host.includes("flipkart.")) {
    return "flipkart";
  }
  throw new Error(`Unsupported retailer for url: ${url}`);
}

async function scrapeProduct(url) {
  const retailer = resolveRetailerFromUrl(url);

  if (retailer === "amazon") {
    return scrapeAmazonProduct(url);
  }

  if (retailer === "flipkart") {
    return scrapeFlipkartProduct(url);
  }

  throw new Error(`Retailer not implemented: ${retailer}`);
}

module.exports = {
  resolveRetailerFromUrl,
  scrapeProduct
};
