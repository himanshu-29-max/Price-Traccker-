(async function () {
  const state = {
    adapter: null,
    productRecord: null,
    range: "all",
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
  state.productRecord = await hydrateFromBackend(state.productRecord);

  await chrome.runtime.sendMessage({
    type: "PRICE_TRACKER_PRODUCT_SEEN",
    payload: state.productRecord
  });

  renderOverlay(state);
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

async function hydrateFromBackend(productRecord) {
  try {
    const syncResult = await window.PriceTrackerApi.syncProduct(productRecord.url);
    const backendProduct = syncResult?.data;
    if (!backendProduct?.id) {
      return productRecord;
    }

    const historyResult = await window.PriceTrackerApi.fetchHistory(backendProduct.id, 180);
    const backendHistory = window.PriceTrackerUtils.toHistoryPoints(
      historyResult?.series?.[0]?.points?.map((point) => ({
        y: point.y,
        x: point.x
      })) || []
    );

    return window.PriceTrackerStorage.upsertProduct(productRecord.key, (current) => ({
      ...(current || {}),
      ...productRecord,
      backendProductId: backendProduct.id,
      backendHistory,
      history: mergeHistory(current?.history || [], backendHistory)
    }));
  } catch (error) {
    return productRecord;
  }
}

function mergeHistory(localHistory, backendHistory) {
  const merged = new Map();
  [...(localHistory || []), ...(backendHistory || [])].forEach((point) => {
    const ts = point.ts || Date.parse(point.x || "");
    if (!Number.isFinite(ts)) {
      return;
    }
    merged.set(ts, {
      price: Number(point.price ?? point.y),
      ts
    });
  });
  return [...merged.values()].sort((left, right) => left.ts - right.ts);
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

function renderOverlay(state) {
  if (document.querySelector("#pt-root")) {
    refreshOverlay(state);
    return;
  }

  const root = document.createElement("aside");
  root.id = "pt-root";
  root.className = "pt-shell";
  root.innerHTML = `
    <button class="pt-launcher" type="button" aria-expanded="true">
      <span class="pt-brand-mark">b</span>
      <span>pricehatke</span>
    </button>
    <section class="pt-panel">
      <header class="pt-topbar">
        <div class="pt-brand">
          <span class="pt-brand-mark">b</span>
          <span class="pt-brand-name">buyhatke style tracker</span>
        </div>
        <div class="pt-actions">
          <button type="button" class="pt-mini-button">Wide</button>
          <button type="button" class="pt-close-button" aria-label="Collapse tracker">-</button>
        </div>
      </header>
      <div class="pt-banner">
        <span class="pt-banner-icon">Hot</span>
        <span id="pt-banner-text"></span>
      </div>
      <section class="pt-history-section">
        <div class="pt-title-row">
          <div>
            <h2 class="pt-section-title">Price history</h2>
            <p class="pt-section-subtitle" id="pt-over-average"></p>
          </div>
          <div class="pt-range-switcher">
            <button type="button" class="pt-range-button" data-range="30">1M</button>
            <button type="button" class="pt-range-button" data-range="90">3M</button>
            <button type="button" class="pt-range-button" data-range="180">6M</button>
            <button type="button" class="pt-range-button" data-range="all">All</button>
          </div>
        </div>
        <div class="pt-history-actions">
          <label class="pt-toggle-row">
            <span>Show best offers</span>
            <input id="pt-best-offer-toggle" type="checkbox" checked />
          </label>
          <span class="pt-linkish">View on tracker</span>
        </div>
        <div id="pt-chart-container"></div>
      </section>
      <section class="pt-stats-grid" id="pt-stats-grid"></section>
      <section class="pt-bottom-grid">
        <article class="pt-card" id="pt-recommend-card"></article>
        <article class="pt-card">
          <div class="pt-card-head">
            <h3>Set price drop alert to buy later</h3>
          </div>
          <form id="pt-alert-form" class="pt-alert-box">
            <input id="pt-target-input" type="number" min="0" placeholder="Target price" />
            <button type="submit">Set price alert</button>
          </form>
          <p class="pt-helper" id="pt-alert-message"></p>
        </article>
      </section>
      <section class="pt-meta-grid">
        <article class="pt-card">
          <div class="pt-card-head">
            <h3>Compare prices</h3>
          </div>
          <div id="pt-compare-box" class="pt-helper"></div>
        </article>
        <article class="pt-card">
          <div class="pt-card-head">
            <h3>Coupon finder</h3>
          </div>
          <div id="pt-coupon-box" class="pt-helper"></div>
        </article>
      </section>
    </section>
  `;

  document.body.append(root);

  root.querySelector(".pt-launcher").addEventListener("click", () => {
    root.classList.toggle("pt-collapsed");
  });

  root.querySelector(".pt-close-button").addEventListener("click", () => {
    root.classList.add("pt-collapsed");
  });

  root.querySelectorAll(".pt-range-button").forEach((button) => {
    button.addEventListener("click", () => {
      state.range = button.dataset.range;
      refreshOverlay(state);
    });
  });

  root.querySelector("#pt-alert-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const input = root.querySelector("#pt-target-input");
    const targetPrice = Number(input.value || 0) || null;
    state.productRecord = await window.PriceTrackerStorage.upsertProduct(state.productRecord.key, (current) => ({
      ...(current || {}),
      ...state.productRecord,
      targetPrice
    }));

    root.querySelector("#pt-alert-message").textContent = targetPrice
      ? `Alert saved for ${window.PriceTrackerUtils.formatMoney(targetPrice)}.`
      : "Target alert cleared.";

    await chrome.runtime.sendMessage({
      type: "PRICE_TRACKER_TARGET_UPDATED",
      payload: state.productRecord
    });

    refreshOverlay(state);
  });

  refreshOverlay(state);
}

async function refreshOverlay(state) {
  const root = document.querySelector("#pt-root");
  if (!root || !state.productRecord) {
    return;
  }

  const { buildRecommendation, buildStats, filterHistoryByDays, formatMoney, formatRelativeTime, lineChartSvg } =
    window.PriceTrackerUtils;

  const compareOffer = await window.PriceTrackerCompare.findComparableOffer({
    ...state.productRecord,
    price: state.productRecord.currentPrice
  });
  const couponState = await window.PriceTrackerCoupons.runCouponDiscovery({
    ...state.adapter,
    price: state.productRecord.currentPrice
  });

  const sourceHistory = state.productRecord.backendHistory?.length
    ? mergeHistory(state.productRecord.history || [], state.productRecord.backendHistory || [])
    : state.productRecord.history || [];
  const rangeDays = state.range === "all" ? "all" : Number(state.range);
  const visibleHistory = filterHistoryByDays(sourceHistory, rangeDays);
  const chartHistory = visibleHistory.length ? visibleHistory : sourceHistory;
  const stats = buildStats(chartHistory);
  const recommendation = buildRecommendation(chartHistory);

  root.querySelector("#pt-banner-text").textContent = buildBannerText(stats, state.productRecord);
  root.querySelector("#pt-over-average").textContent = buildVsAverageText(stats);
  root.querySelector("#pt-chart-container").innerHTML = lineChartSvg(chartHistory);
  root.querySelector("#pt-stats-grid").innerHTML = buildStatsGrid(stats, state.productRecord, compareOffer);
  root.querySelector("#pt-recommend-card").innerHTML = buildRecommendationCard(recommendation, chartHistory.length);
  root.querySelector("#pt-compare-box").innerHTML = buildCompareMarkup(compareOffer, formatMoney);
  root.querySelector("#pt-coupon-box").textContent = couponState.message;
  root.querySelector("#pt-target-input").value = state.productRecord.targetPrice || "";

  const alertMessage = state.productRecord.targetPrice
    ? `Watching for ${formatMoney(state.productRecord.targetPrice)}. Last update ${formatRelativeTime(state.productRecord.updatedAt)}.`
    : `Current price ${formatMoney(state.productRecord.currentPrice)}. Save a threshold to get notified.`;
  root.querySelector("#pt-alert-message").textContent = alertMessage;

  root.querySelectorAll(".pt-range-button").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.range === String(state.range));
  });
}

function buildBannerText(stats, productRecord) {
  if (!stats.current || !stats.lowest) {
    return `Tracking ${productRecord.title} in real time`;
  }
  const savings = Math.max(stats.current - stats.lowest, 0);
  if (!savings) {
    return "Current price is sitting near the tracked low";
  }
  return `Price graphs suggest you could save up to Rs ${savings.toLocaleString()} by timing the buy better`;
}

function buildVsAverageText(stats) {
  if (stats.currentVsAverage == null) {
    return "Not enough history yet to compare against average price";
  }
  const direction = stats.currentVsAverage > 0 ? "higher" : "lower";
  return `${Math.abs(stats.currentVsAverage).toFixed(2)}% ${direction} than average price`;
}

function buildStatsGrid(stats, productRecord, compareOffer) {
  const average = stats.average != null ? stats.average : productRecord.currentPrice;
  const lowest = stats.lowest != null ? stats.lowest : productRecord.currentPrice;
  const highest = stats.highest != null ? stats.highest : productRecord.currentPrice;
  const bestDeal = compareOffer?.price || lowest;
  return [
    statCard("Highest Price", highest, "neutral"),
    statCard("Average Price", average, "neutral"),
    statCard("Lowest Price", lowest, "good"),
    statCard("Current Price", productRecord.currentPrice, "warning"),
    statCard("Best Deal", bestDeal, "good")
  ].join("");
}

function statCard(label, value, tone) {
  return `
    <article class="pt-stat-card tone-${tone}">
      <div class="pt-stat-label">${label}</div>
      <div class="pt-stat-value">Rs ${Math.round(value).toLocaleString()}</div>
    </article>
  `;
}

function buildRecommendationCard(recommendation, sampleSize) {
  return `
    <div class="pt-card-head">
      <h3>Should you buy this now?</h3>
    </div>
    <div class="pt-recommend-pill tone-${recommendation.tone}">${recommendation.label}</div>
    <p class="pt-helper">${recommendation.description}</p>
    <div class="pt-helper">${sampleSize} tracked price points analyzed.</div>
  `;
}

function buildCompareMarkup(compareOffer, formatMoney) {
  if (!compareOffer) {
    return "No lower tracked match found yet. As you browse more stores, this panel will compare them automatically.";
  }
  return `${escapeHtml(compareOffer.site)} currently looks cheaper at ${formatMoney(compareOffer.price)}. Estimated savings: ${formatMoney(compareOffer.difference)}.`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
