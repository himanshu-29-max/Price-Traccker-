import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json, os, time
from datetime import datetime

# --- CONFIG ---
# Apni ScraperAPI key yahan dalo
SCRAPER_API_KEY = "98140924c53c3da8de89d24bccc92568" 

st.set_page_config(page_title="Universal Price Tracker", layout="wide")

def get_live_price(url):
    # render=true se Amazon/Flipkart ko lagta hai real browser hai
    proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}&render=true"
    
    try:
        response = requests.get(proxy_url, timeout=90)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            
            # --- Universal Price Selectors ---
            # Flipkart, Amazon aur general sites ke liye common tags
            selectors = [
                {"class": "Nx9bqj"},          # Flipkart New
                {"id": "priceblock_ourprice"}, # Amazon Old
                {"id": "priceblock_dealprice"},# Amazon Deal
                {"class": "a-price-whole"},    # Amazon New (Common)
                {"class": "_30jeq3"},          # Flipkart Old
                {"id": "offering-price"}       # Others
            ]
            
            price_text = None
            
            # 1. Selectors se dhoondo
            for s in selectors:
                tag = soup.find(None, s) # None matlab kisi bhi tag (div, span) mein dhoondo
                if tag:
                    price_text = tag.text
                    break
            
            # 2. Agar nahi mila toh pure page mein '₹' dhoondo (Backup Plan)
            if not price_text:
                all_text = soup.get_text()
                if "₹" in all_text:
                    # Ye thoda advanced logic hai price nikalne ka
                    return None 

            if price_text:
                # Text se sirf numbers nikalna
                clean_price = ''.join(filter(str.isdigit, price_text))
                return int(clean_price)
        return None
    except:
        return None

# --- UI INTERFACE ---
st.markdown("<h1 style='text-align: center;'>🌐 Universal Price Tracker</h1>", unsafe_allow_with_html=True)
st.info("Amazon, Flipkart aur baaki sites ke links yahan kaam karenge.")

# Sidebar
st.sidebar.header("Settings")
product_url = st.sidebar.text_input("Product Link Dalein (Amazon/Flipkart):")
target_p = st.sidebar.number_input("Target Price (₹):", value=3000)

if st.sidebar.button("Track Price"):
    if product_url:
        with st.spinner("Bypass Engine start ho raha hai... 30-40 seconds lag sakte hain..."):
            curr_p = get_live_price(product_url)
            
            if curr_p:
                st.balloons()
                st.success(f"Success! Current Price mil gaya: ₹{curr_p:,}")
                
                # Metrics Display
                col1, col2 = st.columns(2)
                col1.metric("Live Price", f"₹{curr_p:,}")
                col2.metric("Target Price", f"₹{target_p:,}")

                # Chart Logic
                data_file = "universal_history.json"
                if os.path.exists(data_file):
                    with open(data_file, "r") as f: data = json.load(f)
                else: data = {"history": []}
                
                data["history"].append({"Price": curr_p, "Date": datetime.now().strftime("%d/%m %H:%M")})
                with open(data_file, "w") as f: json.dump(data, f)
                
                df = pd.DataFrame(data["history"])
                st.line_chart(df.set_index("Date"))

                if curr_p <= target_p:
                    st.warning("🔥 Deal Alert! Price aapke target se niche hai!")
            else:
                st.error("Bhai, price nahi nikal paya. Check karo link sahi hai ya API credits khatam toh nahi huye?")
    else:
        st.warning("Pehle link toh dalo!")

if st.sidebar.button("Reset History"):
    if os.path.exists("universal_history.json"):
        os.remove("universal_history.json")
        st.sidebar.success("History deleted!")
