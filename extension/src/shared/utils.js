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
    createProductKey,
    extractDigits,
    formatMoney,
    formatRelativeTime,
    lineChartSvg,
    readFirstText,
    readJsonLdProduct,
    readMetaContent,
    normalizeWhitespace,
    slugify
  };
})();
