(function () {
  const DEFAULT_API_BASE_URL = "http://localhost:4000/api/v1";

  async function getApiBaseUrl() {
    const state = await window.PriceTrackerStorage.readRoot();
    return state.settings?.apiBaseUrl || DEFAULT_API_BASE_URL;
  }

  async function request(path, options = {}) {
    const baseUrl = await getApiBaseUrl();
    const response = await fetch(`${baseUrl}${path}`, {
      headers: {
        "content-type": "application/json",
        ...(options.headers || {})
      },
      ...options
    });

    if (!response.ok) {
      throw new Error(`API request failed with ${response.status}`);
    }

    return response.json();
  }

  async function syncProduct(url) {
    return request("/products/scrape", {
      method: "POST",
      body: JSON.stringify({ url })
    });
  }

  async function fetchHistory(productId, rangeDays) {
    return request(`/products/${productId}/history?rangeDays=${rangeDays}`);
  }

  window.PriceTrackerApi = {
    fetchHistory,
    getApiBaseUrl,
    syncProduct
  };
})();
