function toPriceChartResponse(product, history) {
  return {
    product: {
      id: product.id,
      title: product.title,
      retailer: product.retailer,
      currentPrice: product.current_price,
      currencyCode: product.currency_code
    },
    series: [
      {
        id: "offer_price",
        label: "Offer Price",
        points: history.map((point) => ({
          x: point.scraped_at,
          y: Number(point.offer_price),
          mrp: point.mrp_price ? Number(point.mrp_price) : null,
          availability: point.availability
        }))
      }
    ]
  };
}

module.exports = { toPriceChartResponse };
