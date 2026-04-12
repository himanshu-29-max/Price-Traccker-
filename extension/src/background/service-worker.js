importScripts("../shared/utils.js", "../shared/storage.js");

chrome.runtime.onInstalled.addListener(() => {
  chrome.alarms.create("price-tracker-alert-check", {
    periodInMinutes: 60
  });
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type === "PRICE_TRACKER_PRODUCT_SEEN") {
    evaluateTarget(message.payload);
    sendResponse({ ok: true });
    return;
  }

  if (message?.type === "PRICE_TRACKER_TARGET_UPDATED") {
    evaluateTarget(message.payload);
    sendResponse({ ok: true });
  }
});

chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name !== "price-tracker-alert-check") {
    return;
  }

  const products = await window.PriceTrackerStorage.listProducts();
  Object.values(products).forEach(evaluateTarget);
});

async function evaluateTarget(product) {
  if (!product || !product.targetPrice || !product.currentPrice) {
    return;
  }

  if (product.currentPrice > product.targetPrice) {
    return;
  }

  const existing = await window.PriceTrackerStorage.getProduct(product.key);
  if (existing?.lastTriggeredPrice === product.currentPrice) {
    return;
  }

  const notificationId = `price-target-${product.key}`;
  chrome.notifications.create(notificationId, {
    type: "basic",
    iconUrl:
      "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAQAAADDPmHLAAAB8UlEQVR4Xu3WwW3DMBRF0YtKQ6hAF6EJdCF6EC3AEXQhOkAXogfRgrS0gQk0r6T9f5K1bA8P0wB7v5r5vN5lAAAAAAAAAAAAAMDxjv0Yj8d3lYqv3z4uB7m5bV9fH3mM4f5c4m9e9vH7B6P0v2v2M+P2k3n2r3Kk3pVv2iQ2TQ6Jp2l0lY6s7m+f0qfJQ3QvJ7Qx1k1vGJ4pK7z7j7x8g6Cw8m9T6rT9m4wqYxT4uT1u2q5aE2QdQ3n0mVb6m3KkM1H1V7n6WmG7p6i6H1Q7WmG7g7m6m5m1Q7WmG7p6i6n5m1Q7WmG7p6i6n5m1Q7WmG7p6i6n5m1Q7WmG7p6i6n5m1Q7WmG7p6i6n5m1Q7WmG7p6i6n5m1Q7WmG7o7v2w6mF8m7fY5R3l0qk2m4pK4l7Y6w2Wm9v0f5Vx2m0m0m6o8bK2pY6uQzR8nQwS0qfJQ3QvJ7Qx1k1vGJ4pK7z7j7x8g6Cw8m9T6rT9m4wqYxT4uT1u2q5aE2QdQ3n0mVb6m3KkM1H1V7n6WmG7p6i6H1Q7WmG7j8d4g2+0x6vV6fT6fT6fT6fT6fT6fT6fT6fT6fT6fT6fT6fT6fT6fT6fT6fT6fT6fT6fT6fT6fT6fT6fT6fT6fQAAAAAAAAAAAAAA8A3+A8sX8bLQ9v6cAAAAAElFTkSuQmCC",
    title: "Target price reached",
    message: `${product.title} is now ${window.PriceTrackerUtils.formatMoney(product.currentPrice)}`
  });

  await window.PriceTrackerStorage.upsertProduct(product.key, (current) => ({
    ...(current || {}),
    ...product,
    lastTriggeredPrice: product.currentPrice,
    lastTriggeredAt: Date.now()
  }));
}
