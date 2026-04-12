const { scrapeAndStoreProduct } = require("../services/price-tracking-service");

async function main() {
  const url = process.argv[2];
  if (!url) {
    throw new Error("Usage: npm run scrape:product -- <product-url>");
  }

  const result = await scrapeAndStoreProduct(url);
  console.log(JSON.stringify(result, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
