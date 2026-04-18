(function () {
  const PRODUCT_ID_SEPARATOR = "::";

  function extractDigits(value) {
    const digits = String(value || "").replace(/[^\d]/g, "");
    return digits ? Number(digits) : null;
  }

  function normalizeWhitespace(value) {
    return String(value || "").replace(/\s+/g, " ").trim();
  }

  function slugify(value) {
    return normalizeWhitespace(value)
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/(^-|-$)/g, "");
  }

  function createProductKey(site, title) {
    return `${site}${PRODUCT_ID_SEPARATOR}${slugify(title)}`;
  }

  function formatMoney(price, currencySymbol) {
    if (price == null || Number.isNaN(price)) {
      return "N/A";
    }
    return `${currencySymbol || "Rs"} ${Number(price).toLocaleString()}`;
  }

  function readJsonLdProduct() {
    const scripts = Array.from(document.querySelectorAll('script[type="application/ld+json"]'));
    for (const script of scripts) {
      try {
        const payload = JSON.parse(script.textContent);
        const queue = Array.isArray(payload) ? payload.slice() : [payload];
        while (queue.length) {
          const item = queue.shift();
          if (!item || typeof item !== "object") {
            continue;
          }
          if (Array.isArray(item)) {
            queue.push(...item);
            continue;
          }
          if (item["@graph"]) {
            queue.push(...item["@graph"]);
          }
          const typeValue = item["@type"];
          const typeList = Array.isArray(typeValue) ? typeValue : [typeValue];
          if (typeList.filter(Boolean).includes("Product")) {
            return item;
          }
          if (item.offers) {
            queue.push(item.offers);
          }
        }
      } catch (error) {
        continue;
      }
    }
    return null;
  }

  function readMetaContent(selectors) {
    for (const selector of selectors) {
      const node = document.querySelector(selector);
      const value = node?.getAttribute("content") || node?.textContent;
      if (value && String(value).trim()) {
        return String(value).trim();
      }
    }
    return null;
  }

  function readFirstText(selectors) {
    for (const selector of selectors) {
      const node = document.querySelector(selector);
      const text = normalizeWhitespace(node?.textContent || "");
      if (text) {
        return text;
      }
    }
    return null;
  }

  function formatRelativeTime(timestamp) {
    if (!timestamp) {
      return "just now";
    }
    const deltaSeconds = Math.max(0, Math.round((Date.now() - timestamp) / 1000));
    if (deltaSeconds < 60) {
      return `${deltaSeconds}s ago`;
    }
    if (deltaSeconds < 3600) {
      return `${Math.round(deltaSeconds / 60)}m ago`;
    }
    if (deltaSeconds < 86400) {
      return `${Math.round(deltaSeconds / 3600)}h ago`;
    }
    return `${Math.round(deltaSeconds / 86400)}d ago`;
  }

  function filterHistoryByDays(points, days) {
    if (!Array.isArray(points) || !points.length || days === "all") {
      return Array.isArray(points) ? points : [];
    }
    const cutoff = Date.now() - days * 24 * 60 * 60 * 1000;
    return points.filter((point) => (point.ts || point.xTs || 0) >= cutoff);
  }

  function buildStats(points) {
    if (!points.length) {
      return {
        average: null,
        current: null,
        currentVsAverage: null,
        highest: null,
        lowest: null
      };
    }

    const prices = points.map((point) => Number(point.price));
    const average = prices.reduce((sum, value) => sum + value, 0) / prices.length;
    const current = prices[prices.length - 1];

    return {
      average,
      current,
      currentVsAverage: average ? ((current - average) / average) * 100 : null,
      highest: Math.max(...prices),
      lowest: Math.min(...prices)
    };
  }

  function buildRecommendation(points) {
    const stats = buildStats(points);
    if (!points.length || stats.current == null || stats.average == null) {
      return {
        label: "Need more data",
        tone: "neutral",
        description: "Track this product over time to unlock stronger buy recommendations."
      };
    }

    const ratio = stats.current / Math.max(stats.average, 1);
    if (ratio <= 0.9) {
      return {
        label: "Good time to buy",
        tone: "good",
        description: "Current price is comfortably below its tracked average."
      };
    }
    if (ratio <= 1.05) {
      return {
        label: "Fair deal",
        tone: "okay",
        description: "Current price is near its tracked average range."
      };
    }
    return {
      label: "Wait for a drop",
      tone: "bad",
      description: "Current price is above its tracked average. Setting an alert is safer."
    };
  }

  function toHistoryPoints(points) {
    if (!Array.isArray(points)) {
      return [];
    }
    return points
      .map((point) => {
        const ts = point.ts || point.xTs || Date.parse(point.x || point.scraped_at || "");
        return {
          price: Number(point.price ?? point.y),
          ts: Number.isNaN(ts) ? Date.now() : ts
        };
      })
      .filter((point) => Number.isFinite(point.price))
      .sort((left, right) => left.ts - right.ts);
  }

  function createSparklinePath(points, width, height) {
    if (!points.length) {
      return "";
    }
    const prices = points.map((point) => point.price);
    const min = Math.min(...prices);
    const max = Math.max(...prices);
    const range = Math.max(max - min, 1);

    return points
      .map((point, index) => {
        const x = (index / Math.max(points.length - 1, 1)) * width;
        const y = height - ((point.price - min) / range) * height;
        return `${index === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`;
      })
      .join(" ");
  }

  function lineChartSvg(points) {
    if (!points.length) {
      return '<div class="pt-empty-state">No price history yet. Track this product to start building the graph.</div>';
    }

    const width = 320;
    const height = 120;
    const path = createSparklinePath(points, width, height);
    const prices = points.map((point) => point.price);
    const min = Math.min(...prices);
    const max = Math.max(...prices);

    return `
      <div class="pt-chart-shell">
        <svg viewBox="0 0 ${width} ${height}" class="pt-chart" preserveAspectRatio="none" aria-label="Price history graph">
          <defs>
            <linearGradient id="ptChartFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="rgba(18,120,95,0.35)"></stop>
              <stop offset="100%" stop-color="rgba(18,120,95,0.02)"></stop>
            </linearGradient>
          </defs>
          <path d="${path} L ${width} ${height} L 0 ${height} Z" fill="url(#ptChartFill)"></path>
          <path d="${path}" class="pt-chart-line"></path>
        </svg>
        <div class="pt-chart-range">
          <span>${formatMoney(min)}</span>
          <span>${formatMoney(max)}</span>
        </div>
      </div>
    `;
  }

  window.PriceTrackerUtils = {
    buildRecommendation,
    buildStats,
    createProductKey,
    extractDigits,
    filterHistoryByDays,
    formatMoney,
    formatRelativeTime,
    lineChartSvg,
    readFirstText,
    readJsonLdProduct,
    readMetaContent,
    normalizeWhitespace,
    slugify,
    toHistoryPoints
  };
})();
