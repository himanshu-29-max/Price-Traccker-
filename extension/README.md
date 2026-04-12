# Chrome Extension Architecture

This folder contains a Manifest V3 Chrome extension version of the project.

## Core modules

- `manifest.json`: registers the service worker, popup, permissions, and product-page content scripts.
- `src/content/adapters.js`: site-specific DOM extraction for Amazon and Flipkart.
- `src/content/content-script.js`: injects the overlay UI, records product history, and binds target alerts.
- `src/content/compare.js`: compares the current product against your locally tracked catalog on other sites.
- `src/content/coupons.js`: coupon-finder engine scaffold. It is intentionally conservative and uses saved coupon lists plus estimation logic.
- `src/background/service-worker.js`: handles alert notifications and background alarm checks.
- `src/popup/*`: simple catalog dashboard for the extension action popup.
- `src/shared/*`: utility and storage wrappers around `chrome.storage.local`.

## How the extension works

1. The content script runs on Amazon and Flipkart pages.
2. A site adapter extracts title, price, anchor node, and coupon/check-out hints.
3. The extension stores the latest seen price in `chrome.storage.local`.
4. The injected overlay renders:
   - price history graph
   - target alert form
   - compare-prices box
   - coupon-finder result card
5. The service worker sends notifications when a target price is met.

## Important product notes

- Price history is currently built from extension browsing data. For a true 3-6 month graph on first visit, you need a backend collector or third-party data source.
- Compare prices currently works against products the user has already tracked locally. Production BuyHatke-style comparison needs a catalog-matching backend.
- Coupon finder is implemented as a safe framework plus saved-code evaluation. Real automatic coupon application on every checkout is highly site-specific and should be extended per retailer with explicit adapters and result validation.

## Load in Chrome

1. Open `chrome://extensions`
2. Enable Developer mode
3. Click `Load unpacked`
4. Select the `extension/` folder

## Next production steps

- Add a backend for product normalization, long-term price storage, and cross-site catalog matching.
- Replace heuristic coupon scoring with merchant-specific adapters and explicit DOM/result verification.
- Add icons in `assets/`.
- Add more store adapters and checkout adapters.
