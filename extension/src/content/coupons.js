(function () {
  async function runCouponDiscovery(product) {
    const coupons = await window.PriceTrackerStorage.getCouponsForDomain(product.domain);
    if (!coupons.length) {
      return {
        status: "idle",
        message: "No saved coupons for this site yet."
      };
    }

    if (!product.checkout) {
      return {
        status: "idle",
        message: "Coupon testing is only available on checkout or cart pages."
      };
    }

    const couponInput = document.querySelector(product.coupon.input);
    if (!couponInput) {
      return {
        status: "unsupported",
        message: "This checkout layout does not expose a coupon box the extension can safely automate yet."
      };
    }

    const best = {
      code: null,
      savings: 0
    };

    for (const code of coupons) {
      const simulatedSavings = estimateCouponValue(code, product.price);
      if (simulatedSavings > best.savings) {
        best.code = code;
        best.savings = simulatedSavings;
      }
    }

    return {
      status: best.code ? "success" : "idle",
      message: best.code
        ? `Best saved coupon looks like ${best.code} for about ${window.PriceTrackerUtils.formatMoney(best.savings)} off.`
        : "No promising coupon found in your saved list.",
      best
    };
  }

  function estimateCouponValue(code, price) {
    const upper = String(code).toUpperCase();
    const percentMatch = upper.match(/(\d{1,2})/);
    if (percentMatch) {
      const numeric = Number(percentMatch[1]);
      if (numeric > 0 && numeric <= 80) {
        return Math.round((price * numeric) / 100);
      }
    }
    if (upper.includes("SAVE")) {
      return Math.round(price * 0.08);
    }
    if (upper.includes("WELCOME")) {
      return Math.round(price * 0.05);
    }
    return 0;
  }

  window.PriceTrackerCoupons = {
    runCouponDiscovery
  };
})();
