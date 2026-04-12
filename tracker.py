import json
import os
import re
from datetime import datetime
from urllib.parse import quote_plus, urlparse

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

DATA_FILE = "price_history.json"
SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY", "")
PRICE_SELECTORS = {
    "flipkart": [
        (By.CLASS_NAME, "Nx9bqj"),
        (By.CSS_SELECTOR, "[class*='Nx9bqj']"),
        (By.CSS_SELECTOR, "div._30jeq3"),
        (By.CSS_SELECTOR, "div._16Jk6d"),
    ],
    "amazon": [
        (By.ID, "priceblock_dealprice"),
        (By.ID, "priceblock_ourprice"),
        (By.ID, "priceblock_saleprice"),
        (By.CSS_SELECTOR, ".a-price .a-offscreen"),
    ],
    "generic": [
        (By.CSS_SELECTOR, 'meta[property="product:price:amount"]'),
        (By.CSS_SELECTOR, 'meta[itemprop="price"]'),
        (By.CSS_SELECTOR, "[itemprop='price']"),
        (By.CSS_SELECTOR, ".price"),
        (By.CSS_SELECTOR, "[class*='price']"),
    ],
}

st.set_page_config(page_title="Price Tracker Pro", layout="wide")
st.title("Universal Price Tracker")
st.caption("Track product prices with stronger scraping, smarter history, and a cleaner dashboard.")


def normalize_url(url):
    return url.strip()


def detect_store(url):
    host = urlparse(url).netloc.lower()
    if "flipkart" in host:
        return "flipkart"
    if "amazon" in host:
        return "amazon"
    return "generic"


def extract_price(value):
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    return int(digits) if digits else None


def parse_timestamp(value):
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%d-%m %H:%M"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def format_money(value):
    return f"Rs {value:,.0f}" if value is not None else "N/A"


def build_headers():
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-IN,en;q=0.9",
    }


def parse_product_from_html(html, store):
    soup = BeautifulSoup(html, "html.parser")
    title = extract_title_from_soup(soup)
    price = extract_price_from_soup(soup, store)
    return {"title": title or "Untitled product", "price": price}


def build_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"products": {}}

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        raw = json.load(file)

    if "products" in raw:
        raw.setdefault("products", {})
        return raw

    history = raw.get("history", [])
    migrated_history = []
    for entry in history:
        timestamp = parse_timestamp(entry.get("Date"))
        migrated_history.append(
            {
                "price": entry.get("Price"),
                "checked_at": (
                    timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    if timestamp
                    else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ),
            }
        )

    return {
        "products": {
            "legacy": {
                "title": "Imported history",
                "url": "",
                "target_price": None,
                "history": migrated_history,
            }
        }
    }


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def get_or_create_product(data, url, title=None, target_price=None):
    products = data.setdefault("products", {})
    if url not in products:
        products[url] = {
            "title": title or "Untitled product",
            "url": url,
            "target_price": target_price,
            "history": [],
        }
    product = products[url]
    if title:
        product["title"] = title
    if target_price is not None:
        product["target_price"] = int(target_price)
    return product


def extract_title(driver):
    for locator in [
        (By.CSS_SELECTOR, "span.B_NuCI"),
        (By.CSS_SELECTOR, "div._4rR01T"),
        (By.ID, "productTitle"),
        (By.CSS_SELECTOR, "h1"),
        (By.TAG_NAME, "title"),
    ]:
        try:
            element = driver.find_element(*locator)
            text = element.text.strip()
            if text:
                return text
        except Exception:
            continue
    return "Untitled product"


def extract_title_from_soup(soup):
    for selector in [
        "span.B_NuCI",
        "div._4rR01T",
        "#productTitle",
        "h1",
        'meta[property="og:title"]',
        "title",
    ]:
        node = soup.select_one(selector)
        text = ""
        if node:
            text = node.get("content") or node.get_text(" ", strip=True)
        if text:
            return text.strip()
    return None


def extract_price_from_soup(soup, store):
    selectors = []
    if store == "flipkart":
        selectors.extend(
            [
                "div.Nx9bqj.CxhGGd",
                "div.Nx9bqj",
                "div._30jeq3",
                "div._16Jk6d",
            ]
        )
    elif store == "amazon":
        selectors.extend(
            [
                "#corePriceDisplay_desktop_feature_div .a-price .a-offscreen",
                "#priceblock_dealprice",
                "#priceblock_ourprice",
                "#priceblock_saleprice",
                ".a-price .a-offscreen",
            ]
        )

    selectors.extend(
        [
            'meta[property="product:price:amount"]',
            'meta[itemprop="price"]',
            "[itemprop='price']",
            ".price",
            "[class*='price']",
        ]
    )

    for selector in selectors:
        node = soup.select_one(selector)
        if not node:
            continue
        value = node.get("content") or node.get("value") or node.get_text(" ", strip=True)
        price = extract_price(value)
        if price:
            return price

    for script in soup.select('script[type="application/ld+json"]'):
        try:
            payload = json.loads(script.get_text(strip=True))
        except json.JSONDecodeError:
            continue
        price = extract_price_from_jsonld(payload)
        if price:
            return price

    html = str(soup)
    for pattern in [
        r'"price"\s*:\s*"?(?P<price>\d[\d,\.]*)"?',
        r'"sellingPrice"\s*:\s*"?(?P<price>\d[\d,\.]*)"?',
        r'"finalPrice"\s*:\s*"?(?P<price>\d[\d,\.]*)"?',
        r'"offerPrice"\s*:\s*"?(?P<price>\d[\d,\.]*)"?',
    ]:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            price = extract_price(match.group("price"))
            if price:
                return price

    return None


def extract_price_from_jsonld(payload):
    queue = payload if isinstance(payload, list) else [payload]
    while queue:
        current = queue.pop(0)
        if isinstance(current, list):
            queue.extend(current)
            continue
        if not isinstance(current, dict):
            continue
        if "@graph" in current and isinstance(current["@graph"], list):
            queue.extend(current["@graph"])

        offers = current.get("offers")
        if isinstance(offers, dict):
            for key in ["price", "lowPrice", "highPrice"]:
                price = extract_price(offers.get(key))
                if price:
                    return price
        if isinstance(offers, list):
            queue.extend(offers)

        for key in ["price", "lowPrice", "highPrice"]:
            price = extract_price(current.get(key))
            if price:
                return price
    return None


def dismiss_store_popups(driver, store):
    if store != "flipkart":
        return
    for locator in [
        (By.CSS_SELECTOR, "button._2KpZ6l._2doB4z"),
        (By.CSS_SELECTOR, "button[class*='_2doB4z']"),
    ]:
        try:
            button = WebDriverWait(driver, 3).until(EC.element_to_be_clickable(locator))
            button.click()
            return
        except Exception:
            continue


def read_price_from_page(driver, store):
    selectors = PRICE_SELECTORS.get(store, []) + PRICE_SELECTORS["generic"]
    for by, selector in selectors:
        try:
            element = WebDriverWait(driver, 4).until(
                EC.presence_of_element_located((by, selector))
            )
            price = extract_price(
                element.text
                or element.get_attribute("content")
                or element.get_attribute("value")
            )
            if price:
                return price
        except Exception:
            continue

    page_text = driver.page_source
    meta_match = re.search(
        r'<meta[^>]+(?:property|itemprop)=["\'](?:product:price:amount|price)["\'][^>]+content=["\'](?P<price>[^"\']+)["\']',
        page_text,
        re.IGNORECASE,
    )
    if meta_match:
        return extract_price(meta_match.group("price"))

    match = re.search(r'"price"\s*:\s*"?(?P<price>\d[\d,\.]*)"?', page_text)
    if match:
        return extract_price(match.group("price"))
    return None


def scrape_with_requests(url, store):
    try:
        response = requests.get(url, headers=build_headers(), timeout=30)
        response.raise_for_status()
    except Exception:
        return {"title": None, "price": None}

    parsed = parse_product_from_html(response.text, store)
    return parsed


def scrape_with_api(url, store):
    if not SCRAPER_API_KEY:
        return {"title": None, "price": None}

    proxy_url = (
        "http://api.scraperapi.com?api_key="
        f"{SCRAPER_API_KEY}&url={quote_plus(url)}&render=true&wait=5000"
    )

    try:
        response = requests.get(proxy_url, timeout=120)
        response.raise_for_status()
    except Exception:
        return {"title": None, "price": None}

    soup = BeautifulSoup(response.content, "html.parser")

    title = None
    for selector in ["span.B_NuCI", "#productTitle", "h1", "title"]:
        node = soup.select_one(selector)
        if node and node.get_text(strip=True):
            title = node.get_text(strip=True)
            break

    price_candidates = []
    if store == "flipkart":
        price_candidates.extend(
            [
                soup.select_one("div.Nx9bqj.C6R3Y2"),
                soup.select_one("div.Nx9bqj"),
            ]
        )
    if store == "amazon":
        price_candidates.extend(
            [
                soup.select_one("span.a-price-whole"),
                soup.select_one(".a-price .a-offscreen"),
            ]
        )
    price_candidates.extend(
        [
            soup.select_one("[itemprop='price']"),
            soup.select_one(".price"),
            soup.select_one("[class*='price']"),
        ]
    )

    for candidate in price_candidates:
        if not candidate:
            continue
        price = extract_price(candidate.get_text(" ", strip=True) or candidate.get("content"))
        if price:
            return {"title": title, "price": price}

    return {"title": title, "price": None}


def get_live_product_details(url):
    store = detect_store(url)
    try:
        driver = build_driver()
        try:
            driver.get(url)
            WebDriverWait(driver, 20).until(
                lambda current_driver: current_driver.execute_script("return document.readyState")
                == "complete"
            )
            dismiss_store_popups(driver, store)
            title = extract_title(driver)
            price = read_price_from_page(driver, store)
            if price is not None:
                return {"title": title, "price": price, "store": store}

            parsed_html = parse_product_from_html(driver.page_source, store)
            if parsed_html["price"] is not None:
                return {
                    "title": parsed_html["title"],
                    "price": parsed_html["price"],
                    "store": store,
                }
        finally:
            driver.quit()
    except Exception:
        pass

    requests_fallback = scrape_with_requests(url, store)
    if requests_fallback["price"] is not None:
        return {
            "title": requests_fallback["title"],
            "price": requests_fallback["price"],
            "store": store,
        }

    fallback = scrape_with_api(url, store)
    return {
        "title": fallback["title"] or "Untitled product",
        "price": fallback["price"],
        "store": store,
    }


def append_price_point(product, price):
    product.setdefault("history", []).append(
        {
            "price": price,
            "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    )


def product_history_frame(product):
    history = product.get("history", [])
    frame = pd.DataFrame(history)
    if frame.empty:
        return frame
    frame["checked_at"] = pd.to_datetime(frame["checked_at"])
    return frame.sort_values("checked_at")


def product_summary(product):
    frame = product_history_frame(product)
    if frame.empty:
        return None

    latest = int(frame["price"].iloc[-1])
    first = int(frame["price"].iloc[0])
    lowest = int(frame["price"].min())
    highest = int(frame["price"].max())
    average = float(frame["price"].mean())
    previous = int(frame["price"].iloc[-2]) if len(frame) > 1 else None
    return {
        "latest": latest,
        "first": first,
        "lowest": lowest,
        "highest": highest,
        "average": average,
        "previous": previous,
        "checks": len(frame),
        "frame": frame,
    }


def render_product_dashboard(product):
    summary = product_summary(product)
    if not summary:
        st.info("No price history available for this product yet.")
        return

    latest = summary["latest"]
    previous = summary["previous"]
    target_price = product.get("target_price")

    top_cols = st.columns(4)
    top_cols[0].metric(
        "Current price",
        format_money(latest),
        None if previous is None else format_money(latest - previous),
    )
    top_cols[1].metric("Lowest seen", format_money(summary["lowest"]))
    top_cols[2].metric("Highest seen", format_money(summary["highest"]))
    top_cols[3].metric("Average", format_money(summary["average"]))

    if target_price:
        if latest <= target_price:
            st.success(
                f"Target hit: {format_money(latest)} is at or below your target of {format_money(target_price)}."
            )
        else:
            st.warning(f"Need {format_money(latest - target_price)} more drop to reach target.")

    frame = summary["frame"].copy()
    frame["Checked At"] = frame["checked_at"]
    frame["Price"] = frame["price"]

    st.plotly_chart(
        px.line(
            frame,
            x="Checked At",
            y="Price",
            markers=True,
            title="Price trend",
            template="plotly_white",
        ),
        use_container_width=True,
    )

    recent = frame[["Checked At", "Price"]].sort_values("Checked At", ascending=False).head(10)
    st.dataframe(recent, use_container_width=True, hide_index=True)
    st.download_button(
        "Download history as CSV",
        data=frame[["Checked At", "Price"]].to_csv(index=False).encode("utf-8"),
        file_name="price_history.csv",
        mime="text/csv",
    )


data = load_data()

st.sidebar.header("Tracker settings")
url_input = normalize_url(st.sidebar.text_input("Product link"))
target_price = st.sidebar.number_input("Target price (Rs)", min_value=0, value=3000, step=100)

if st.sidebar.button("Update price", use_container_width=True):
    if not url_input:
        st.sidebar.error("Enter a product link first.")
    elif not url_input.startswith(("http://", "https://")):
        st.error("Please enter the full product URL, including https://")
    else:
        with st.spinner("Fetching the latest product price..."):
            details = get_live_product_details(url_input)
            if details["price"] is None:
                st.error("Could not detect the product price on that page.")
                st.info(
                    "Make sure you pasted the direct product page URL. Flipkart search, listing, or redirected pages usually do not expose a stable product price."
                )
            else:
                product = get_or_create_product(
                    data,
                    url_input,
                    title=details["title"],
                    target_price=target_price,
                )
                append_price_point(product, details["price"])
                save_data(data)

                st.success(f"Updated {product['title']}")
                if len(product.get("history", [])) == 1:
                    st.balloons()

products = data.get("products", {})

if st.sidebar.button("Clear all history", use_container_width=True):
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
    st.sidebar.success("Saved history cleared.")
    st.rerun()

if not products:
    st.info("Add a product link from the sidebar and click Update price to build your tracker.")
else:
    product_options = {
        f"{item.get('title', 'Untitled product')} ({detect_store(url).title()})": url
        for url, item in products.items()
    }
    selected_label = st.selectbox("Tracked products", list(product_options.keys()))
    selected_url = product_options[selected_label]
    selected_product = products[selected_url]

    st.subheader(selected_product.get("title", "Tracked product"))
    if selected_product.get("url"):
        st.caption(selected_product["url"])

    summary = product_summary(selected_product)
    if summary:
        trend = summary["latest"] - summary["first"]
        trend_label = "up" if trend > 0 else "down" if trend < 0 else "flat"
        st.write(
            f"{summary['checks']} checks recorded. Overall trend is {trend_label} by {format_money(abs(trend))} since the first capture."
        )

    render_product_dashboard(selected_product)
