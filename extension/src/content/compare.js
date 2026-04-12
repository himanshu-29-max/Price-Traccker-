(function () {
  async function findComparableOffer(product) {
    const products = await window.PriceTrackerStorage.listProducts();
    const currentTitle = window.PriceTrackerUtils.slugify(product.title);
    const offers = Object.values(products)
      .filter((item) => item && item.title)
      .filter((item) => item.site !== product.site)
      .map((item) => {
        const similarity = titleOverlapScore(currentTitle, window.PriceTrackerUtils.slugify(item.title));
        return { ...item, similarity };
      })
      .filter((item) => item.similarity >= 0.6 && typeof item.currentPrice === "number")
      .sort((left, right) => left.currentPrice - right.currentPrice);

    if (!offers.length) {
      return null;
    }

    const best = offers[0];
    if (best.currentPrice >= product.price) {
      return null;
    }

    return {
      site: best.site,
      title: best.title,
      price: best.currentPrice,
      url: best.url,
      difference: product.price - best.currentPrice
    };
  }

  function titleOverlapScore(left, right) {
    const leftTokens = new Set(left.split("-").filter(Boolean));
    const rightTokens = new Set(right.split("-").filter(Boolean));
    const intersection = [...leftTokens].filter((token) => rightTokens.has(token)).length;
    const union = new Set([...leftTokens, ...rightTokens]).size || 1;
    return intersection / union;
  }

  window.PriceTrackerCompare = {
    findComparableOffer
  };
})();
