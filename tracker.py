import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json, os
from datetime import datetime

# --- CONFIG (Apni API Key yahan dalo) ---
# ScraperAPI dashboard se key copy karke yahan paste karo
SCRAPER_API_KEY =98140924c53c3da8de89d24bccc92568 

st.set_page_config(page_title="Price Tracker Pro", layout="wide")

def get_live_price(url):
    # Proxy URL jo Flipkart ko chakma degi
    proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}"
    
    try:
        # ScraperAPI ko request bhej rahe hain
        response = requests.get(proxy_url, timeout=60) 
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            # Flipkart ka price wala naya tag
            tag = soup.find("div", {"class": "Nx9bqj"})
            if tag:
                price_text = tag.text.replace("₹", "").replace(",", "")
                return int(float(price_text))
        return None
    except Exception as e:
        st.error(f"API Error: {e}")
        return None

# --- UI LOGIC ---
st.title("🛡️ Smart Tracker (Bypass Mode)")

product_url = st.sidebar.text_input("Flipkart Link Yahan Dalein:")
target_price = st.sidebar.number_input("Target Price (₹):", value=3000)

if st.sidebar.button("Update Price"):
    if product_url and SCRAPER_API_KEY != "PASTE_YOUR_KEY_HERE":
        with st.spinner("Proxy Engine se bypass kar raha hoon... isme 20-30 seconds lag sakte hain..."):
            current_price = get_live_price(product_url)
            
            if current_price:
                st.balloons()
                st.metric("Live Price", f"₹{current_price:,}")
                
                # History chart logic (Simple)
                st.info(f"Price mil gaya! Agla target ₹{target_price} hai.")
            else:
                st.error("Bhai, API ne bhi kaam nahi kiya. Check karo API Key sahi hai ya limit khatam ho gayi.")
    else:
        st.warning("Pehle API Key (code mein) aur Link (screen par) dalo!")
