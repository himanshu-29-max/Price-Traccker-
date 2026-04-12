(function () {
  const ROOT_KEY = "priceTrackerState";

  const defaultState = {
    products: {},
    couponsByDomain: {
      "amazon.in": ["SAVE10", "WELCOME5"],
      "amazon.com": ["WELCOME10", "SPRING15"],
      "flipkart.com": ["NEWUSER", "SUPERCOIN"]
    },
    settings: {
      compareWindowDays: 180
    }
  };

  function readRoot() {
    return new Promise((resolve) => {
      chrome.storage.local.get([ROOT_KEY], (result) => {
        resolve({ ...defaultState, ...(result[ROOT_KEY] || {}) });
      });
    });
  }

  function writeRoot(state) {
    return new Promise((resolve) => {
      chrome.storage.local.set({ [ROOT_KEY]: state }, resolve);
    });
  }

  async function upsertProduct(productKey, updater) {
    const state = await readRoot();
    const current = state.products[productKey] || null;
    state.products[productKey] = updater(current);
    await writeRoot(state);
    return state.products[productKey];
  }

  async function listProducts() {
    const state = await readRoot();
    return state.products;
  }

  async function getProduct(productKey) {
    const state = await readRoot();
    return state.products[productKey] || null;
  }

  async function recordProductSnapshot(snapshot) {
    return upsertProduct(snapshot.key, (current) => {
      const history = Array.isArray(current?.history) ? current.history.slice() : [];
      const latest = history[history.length - 1];
      if (!latest || latest.price !== snapshot.currentPrice) {
        history.push({
          price: snapshot.currentPrice,
          ts: snapshot.updatedAt
        });
      }

      return {
        ...(current || {}),
        ...snapshot,
        history: history.slice(-720)
      };
    });
  }

  async function getCouponsForDomain(domain) {
    const state = await readRoot();
    return state.couponsByDomain[domain] || [];
  }

  async function setCouponsForDomain(domain, coupons) {
    const state = await readRoot();
    state.couponsByDomain[domain] = coupons;
    await writeRoot(state);
  }

  window.PriceTrackerStorage = {
    getCouponsForDomain,
    getProduct,
    listProducts,
    recordProductSnapshot,
    readRoot,
    setCouponsForDomain,
    upsertProduct,
    writeRoot
  };
})();
