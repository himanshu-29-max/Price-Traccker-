(async function initPopup() {
  const container = document.getElementById("popup-products");
  const products = Object.values(await window.PriceTrackerStorage.listProducts()).sort(
    (left, right) => (right.updatedAt || 0) - (left.updatedAt || 0)
  );

  if (!products.length) {
    container.innerHTML = '<p class="popup-empty">No tracked products yet. Visit an Amazon or Flipkart product page to start.</p>';
    return;
  }

  container.innerHTML = products
    .map((product) => {
      const latestHistory = (product.history || []).slice(-30);
      return `
        <article class="popup-card">
          <h2>${escapeHtml(product.title)}</h2>
          <div class="popup-meta">
            <span>${product.site}</span>
            <span>${window.PriceTrackerUtils.formatMoney(product.currentPrice)}</span>
          </div>
          <div class="popup-meta">
            <span>${product.targetPrice ? `Target ${window.PriceTrackerUtils.formatMoney(product.targetPrice)}` : "No target"}</span>
            <span>${window.PriceTrackerUtils.formatRelativeTime(product.updatedAt)}</span>
          </div>
          ${window.PriceTrackerUtils.lineChartSvg(latestHistory)}
        </article>
      `;
    })
    .join("");
})();

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
