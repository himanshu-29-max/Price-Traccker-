import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json, os, re
from datetime import datetime

# --- CONFIG ---
SCRAPER_API_KEY = "98140924c53c3da8de89d24bccc92568" 

st.set_page_config(page_title="Universal Price Tracker", layout="wide")

def get_live_price(url):
    # render=true aur wait=10000 taaki JavaScript poori tarah load ho jaye
    proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}&render=true&wait=10000"
    
    try:
        response = requests.get(proxy_url, timeout=120)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            
            # 1. Sabse pehle standard classes try karo (Flipkart/Amazon)
            selectors = [
                {"class": "Nx9bqj"},          # Flipkart New
                {"class": "a-price-whole"},    # Amazon
                {"class": "Nx9bqj C6R3Y2"},   # Flipkart Variant
                {"class": "_30jeq3"},          # Flipkart Old
                {"id": "priceblock_ourprice"}  # Amazon Old
            ]
            
            for s in selectors:
                tag = soup.find(None, s)
                if tag:
                    price_text = tag.text
                    clean_price = ''.join(filter(str.isdigit, price_text))
                    if clean_price:
                        return int(clean_price)
            
            # 2. Backup Plan: Pure page mein '₹' ke baad wale numbers dhoondo
            page_text = soup.get_text()
            # Regex to find price like ₹ 1,499 or ₹1499
            regex_prices = re.findall(r'₹\s?([0-9,]+)', page_text)
            if regex_prices:
                # Pehla valid number uthao jo 100 se bada ho (taaki koi random chota number na aaye)
                for p in regex_prices:
                    val = int(p.replace(',', ''))
                    if val > 100:
                        return val
                        
        return None
    except Exception as e:
        return None

# --- UI INTERFACE ---
st.title("🛡️ Universal Price Tracker")
st.write("Flipkart aur Amazon ke products ka price track karein.")

# Sidebar
st.sidebar.header("Settings")
product_url = st.sidebar.text_input("Product Link (Complete URL):")
target_p = st.sidebar.number_input("Target Price (Rs):", value=3000)

if st.sidebar.button("Track Price"):
    if product_url:
        if "http" not in product_url:
            st.error("Bhai, poora link dalo (https://...)")
        else:
            with st.spinner("Proxy Engine bypass kar raha hai... isme 40-60 seconds lag sakte hain..."):
                curr_p = get_live_price(product_url)
                
                if curr_p:
                    st.balloons()
                    st.success(f"Success! Price mil gaya: Rs {curr_p:,}")
                    
                    # Metrics
                    c1, c2 = st.columns(2)
                    c1.metric("Live Price", f"Rs {curr_p:,}")
                    c2.metric("Target Price", f"Rs {target_p:,}")

                    # History Management
                    data_file = "price_log.json"
                    if os.path.exists(data_file):
                        with open(data_file, "r") as f: data = json.load(f)
                    else: data = {"history": []}
                    
                    data["history"].append({"Price": curr_p, "Date": datetime.now().strftime("%d-%m %H:%M")})
                    with open(data_file, "w") as f: json.dump(data, f)
                    
                    # Graph
                    df = pd.DataFrame(data["history"])
                    st.line_chart(df.set_index("Date"))
                else:
                    st.error("Price fetch nahi ho paya. Ek baar link check karo ki browser mein poora page khul raha hai na?")
    else:
        st.warning("Link dalein bina kaam nahi chalega!")

if st.sidebar.button("Reset History"):
    if os.path.exists("price_log.json"):
        os.remove("price_log.json")
        st.sidebar.success("History deleted!")
