(function () {
  const {
    extractDigits,
    normalizeWhitespace,
    readFirstText,
    readJsonLdProduct,
    readMetaContent
  } = window.PriceTrackerUtils;

  function resolveStructuredPrice() {
    const jsonLd = readJsonLdProduct();
    const offerPrice =
      jsonLd?.offers?.price ||
      jsonLd?.offers?.lowPrice ||
      jsonLd?.price ||
      readMetaContent([
        'meta[property="product:price:amount"]',
        'meta[name="price"]',
        'meta[name="twitter:data1"]'
      ]);
    return extractDigits(offerPrice);
  }

  function resolveStructuredTitle() {
    const jsonLd = readJsonLdProduct();
    return normalizeWhitespace(
      jsonLd?.name ||
        readMetaContent(['meta[property="og:title"]', 'meta[name="title"]']) ||
        document.title
    );
  }

  function resolveAnchor(selectors) {
    for (const selector of selectors) {
      const node = document.querySelector(selector);
      if (node) {
        return node;
      }
    }
    return document.body;
  }

  function amazonProductAdapter() {
    const title =
      readFirstText(["#productTitle", "#title span", "h1.a-size-large"]) ||
      resolveStructuredTitle();
    const price =
      extractDigits(
        readFirstText([
          "#corePriceDisplay_desktop_feature_div .a-price .a-offscreen",
          "#priceblock_dealprice",
          "#priceblock_ourprice",
          "#priceblock_saleprice",
          ".a-price .a-offscreen"
        ])
      ) || resolveStructuredPrice();
    const anchor = resolveAnchor(["#dp-container", "#centerCol", "#ppd", "#dp"]);

    if (!title || !price || !anchor) {
      return null;
    }

    return {
      site: "amazon",
      domain: location.hostname,
      currencySymbol: "Rs",
      title,
      price,
      anchor,
      url: location.href,
      checkout: detectCheckoutPage(),
      coupon: {
        input: 'input[name*="coupon"], input[placeholder*="coupon" i], input[placeholder*="promo" i]',
        applyButton: 'button, input[type="submit"]'
      }
    };
  }

  function flipkartProductAdapter() {
    const title =
      readFirstText(["span.B_NuCI", "div._4rR01T", "h1", "span.VU-ZEz"]) ||
      resolveStructuredTitle();
    const price =
      extractDigits(
        readFirstText([
          "div.Nx9bqj.CxhGGd",
          "div.Nx9bqj",
          "[class*='Nx9bqj']",
          "div._30jeq3",
          "div._16Jk6d"
        ])
      ) || resolveStructuredPrice();
    const anchor = resolveAnchor([
      "div._1YokD2._2GoDe3",
      "div._16FRp0",
      "div._1AtVbE",
      "div._2cM9lP",
      "div._1UhVsV"
    ]);

    if (!title || !price || !anchor) {
      return null;
    }

    return {
      site: "flipkart",
      domain: location.hostname,
      currencySymbol: "Rs",
      title,
      price,
      anchor,
      url: location.href,
      checkout: detectCheckoutPage(),
      coupon: {
        input: 'input[placeholder*="coupon" i], input[placeholder*="promo" i]',
        applyButton: "button"
      }
    };
  }

  function detectCheckoutPage() {
    const href = location.href.toLowerCase();
    return ["checkout", "payment", "cart", "buy", "basket"].some((term) => href.includes(term));
  }

  function getAdapter() {
    const host = location.hostname;
    if (host.includes("amazon.")) {
      return amazonProductAdapter();
    }
    if (host.includes("flipkart.")) {
      return flipkartProductAdapter();
    }
    return null;
  }

  window.PriceTrackerAdapters = {
    detectCheckoutPage,
    getAdapter
  };
})();
