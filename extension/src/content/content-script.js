(async function () {
  const state = {
    adapter: null,
    productRecord: null,
    timer: null,
    observer: null
  };

  await bootstrap(state);
})();

async function bootstrap(state) {
  const adapter = await waitForProductAdapter();
  if (!adapter || typeof adapter.price !== "number") {
    return;
  }

  state.adapter = adapter;
  state.productRecord = await persistSnapshot(adapter);
  await chrome.runtime.sendMessage({
    type: "PRICE_TRACKER_PRODUCT_SEEN",
    payload: state.productRecord
  });

  await renderOverlay(state);
  wireRealtimeTracking(state);
}

async function waitForProductAdapter() {
  for (let attempt = 0; attempt < 40; attempt += 1) {
    const adapter = window.PriceTrackerAdapters.getAdapter();
    if (adapter && typeof adapter.price === "number") {
      return adapter;
    }
    await new Promise((resolve) => window.setTimeout(resolve, 750));
  }
  return null;
}

async function persistSnapshot(adapter) {
  const { createProductKey } = window.PriceTrackerUtils;
  return window.PriceTrackerStorage.recordProductSnapshot({
    key: createProductKey(adapter.site, adapter.title),
    site: adapter.site,
    title: adapter.title,
    url: adapter.url,
    domain: adapter.domain,
    currencySymbol: adapter.currencySymbol,
    currentPrice: adapter.price,
    updatedAt: Date.now()
  });
}

async function renderOverlay(state) {
  const { adapter, productRecord } = state;
  const { lineChartSvg, formatMoney, formatRelativeTime } = window.PriceTrackerUtils;
  if (document.querySelector("#pt-root")) {
    refreshOverlay(state);
    return;
  }

  const compareOffer = await window.PriceTrackerCompare.findComparableOffer({
    ...productRecord,
    price: productRecord.currentPrice
  });

  const couponState = await window.PriceTrackerCoupons.runCouponDiscovery({
    ...adapter,
    price: productRecord.currentPrice
  });

  const root = document.createElement("aside");
  root.id = "pt-root";
  root.className = "pt-shell";
  root.innerHTML = `
    <button class="pt-toggle" type="button" aria-expanded="true">Price Tracker Pro</button>
    <section class="pt-panel">
      <header class="pt-header">
        <div>
          <p class="pt-kicker">${adapter.site.toUpperCase()}</p>
          <h2 class="pt-title">${escapeHtml(productRecord.title)}</h2>
          <div class="pt-live-row">
            <span class="pt-live-dot"></span>
            <span id="pt-live-status">Live tracking • updated ${formatRelativeTime(productRecord.updatedAt)}</span>
          </div>
        </div>
        <div>
          <div class="pt-price" id="pt-current-price">${formatMoney(productRecord.currentPrice, adapter.currencySymbol)}</div>
          <div class="pt-helper" id="pt-price-delta">${buildPriceDeltaText(productRecord)}</div>
        </div>
      </header>
      <div class="pt-section">
        <div class="pt-section-head">
          <span>Price history</span>
          <span>${productRecord.history.length} points</span>
        </div>
        <div id="pt-chart-container">${lineChartSvg(productRecord.history)}</div>
      </div>
      <div class="pt-section">
        <div class="pt-section-head">
          <span>Target alert</span>
          <span>${productRecord.targetPrice ? formatMoney(productRecord.targetPrice) : "Not set"}</span>
        </div>
        <form id="pt-alert-form" class="pt-alert-form">
          <input id="pt-target-input" type="number" min="0" placeholder="Set target price" value="${productRecord.targetPrice || ""}" />
          <button type="submit">Save</button>
        </form>
        <p class="pt-helper" id="pt-alert-message">
          ${productRecord.targetPrice && productRecord.currentPrice <= productRecord.targetPrice
            ? "Target reached. You should get a notification from the extension."
            : "Set a target and the background worker will notify you when this page price drops to that level."}
        </p>
      </div>
      <div class="pt-section">
        <div class="pt-section-head">
          <span>Compare prices</span>
          <span>${compareOffer ? "Found" : "No lower match"}</span>
        </div>
        <div class="pt-compare-box">
          ${
            compareOffer
              ? `<strong>${compareOffer.site}</strong> has a lower tracked price at ${formatMoney(compareOffer.price)}.
                 <div class="pt-helper">You may save about ${formatMoney(compareOffer.difference)} if it is the same product variant.</div>`
              : '<div class="pt-helper">As you browse more stores, the extension will compare against your tracked catalog automatically.</div>'
          }
        </div>
      </div>
      <div class="pt-section">
        <div class="pt-section-head">
          <span>Coupon finder</span>
          <span>${couponState.status}</span>
        </div>
        <div class="pt-helper">${escapeHtml(couponState.message)}</div>
      </div>
    </section>
  `;

  adapter.anchor.prepend(root);

  root.querySelector(".pt-toggle").addEventListener("click", () => {
    const expanded = root.classList.toggle("pt-collapsed");
    root.querySelector(".pt-toggle").setAttribute("aria-expanded", String(!expanded));
  });

  root.querySelector("#pt-alert-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const input = root.querySelector("#pt-target-input");
    const targetPrice = Number(input.value || 0) || null;
    const updated = await window.PriceTrackerStorage.upsertProduct(productRecord.key, (current) => ({
      ...current,
      targetPrice
    }));

    root.querySelector("#pt-alert-message").textContent = targetPrice
      ? `Alert saved for ${formatMoney(targetPrice)}.`
      : "Target price cleared.";

    await chrome.runtime.sendMessage({
      type: "PRICE_TRACKER_TARGET_UPDATED",
      payload: updated
    });
  });

  refreshOverlay(state);
}

function wireRealtimeTracking(state) {
  state.timer = window.setInterval(() => refreshSnapshot(state), 30000);
  state.observer = new MutationObserver(() => {
    window.clearTimeout(state.mutationDebounce);
    state.mutationDebounce = window.setTimeout(() => refreshSnapshot(state), 1200);
  });

  state.observer.observe(document.body, {
    childList: true,
    subtree: true,
    characterData: true
  });
}

async function refreshSnapshot(state) {
  const adapter = window.PriceTrackerAdapters.getAdapter();
  if (!adapter || typeof adapter.price !== "number") {
    return;
  }

  const previousPrice = state.productRecord?.currentPrice;
  state.adapter = adapter;
  state.productRecord = await persistSnapshot(adapter);

  if (previousPrice !== state.productRecord.currentPrice) {
    await chrome.runtime.sendMessage({
      type: "PRICE_TRACKER_PRODUCT_SEEN",
      payload: state.productRecord
    });
  }

  refreshOverlay(state);
}

async function refreshOverlay(state) {
  const root = document.querySelector("#pt-root");
  if (!root || !state.productRecord) {
    return;
  }

  const { formatMoney, formatRelativeTime, lineChartSvg } = window.PriceTrackerUtils;
  const compareOffer = await window.PriceTrackerCompare.findComparableOffer({
    ...state.productRecord,
    price: state.productRecord.currentPrice
  });

  root.querySelector("#pt-current-price").textContent = formatMoney(
    state.productRecord.currentPrice,
    state.adapter.currencySymbol
  );
  root.querySelector("#pt-live-status").textContent = `Live tracking • updated ${formatRelativeTime(
    state.productRecord.updatedAt
  )}`;
  root.querySelector("#pt-price-delta").textContent = buildPriceDeltaText(state.productRecord);
  root.querySelector("#pt-chart-container").innerHTML = lineChartSvg(state.productRecord.history);

  const compareHead = root.querySelector(".pt-section:nth-of-type(3) .pt-section-head span:last-child");
  const compareBox = root.querySelector(".pt-compare-box");
  if (compareOffer) {
    compareHead.textContent = "Found";
    compareBox.innerHTML = `<strong>${escapeHtml(compareOffer.site)}</strong> has a lower tracked price at ${formatMoney(
      compareOffer.price
    )}.<div class="pt-helper">You may save about ${formatMoney(compareOffer.difference)} if it is the same product variant.</div>`;
  } else {
    compareHead.textContent = "No lower match";
    compareBox.innerHTML =
      '<div class="pt-helper">As you browse more stores, the extension will compare against your tracked catalog automatically.</div>';
  }
}

function buildPriceDeltaText(productRecord) {
  const history = productRecord.history || [];
  if (history.length < 2) {
    return "First tracked price point";
  }
  const latest = history[history.length - 1].price;
  const previous = history[history.length - 2].price;
  const delta = latest - previous;
  if (delta === 0) {
    return "No change from last check";
  }
  return delta < 0 ? `Down by Rs ${Math.abs(delta).toLocaleString()}` : `Up by Rs ${delta.toLocaleString()}`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
