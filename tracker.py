import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json, os
from datetime import datetime

# --- CONFIG (Apni API Key yahan dalo) ---
SCRAPER_API_KEY = "TUMHARI_API_KEY_YAHAN_DALO"

st.set_page_config(page_title="Price Master Pro", layout="wide")

def get_live_price(url):
    # ScraperAPI ka link banaya
    proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}"
    
    try:
        response = requests.get(proxy_url, timeout=30)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            # Flipkart price tag
            tag = soup.find("div", {"class": "Nx9bqj"})
            if tag:
                return int(''.join(filter(str.isdigit, tag.text)))
        return None
    except:
        return None

# --- UI ---
st.title("💰 Smart Price Tracker (Pro Edition)")

product_url = st.sidebar.text_input("Flipkart Link:")
target_price = st.sidebar.number_input("Target Price (₹):", value=3000)

if st.sidebar.button("Update Price"):
    if product_url and SCRAPER_API_KEY != "TUMHARI_API_KEY_YAHAN_DALO":
        with st.spinner("Proxy Engine se bypass kar raha hoon... thoda sabar karein..."):
            current_price = get_live_price(product_url)
            
            if current_price:
                st.balloons()
                st.metric("Live Price", f"₹{current_price:,}")
                # (Baki chart wala logic waisa hi rahega)
            else:
                st.error("Bhai, Proxy ne bhi jawab de diya. Link check karo ya thodi der baad try karo.")
    else:
        st.warning("Pehle API Key aur Link dalo!")
