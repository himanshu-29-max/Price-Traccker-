import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json, os, time
from datetime import datetime

# --- CONFIG ---
SCRAPER_API_KEY = "98140924c53c3da8de89d24bccc92568" 

st.set_page_config(page_title="Universal Price Tracker", layout="wide")

def get_live_price(url):
    proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}&render=true"
    try:
        response = requests.get(proxy_url, timeout=90)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            selectors = [
                {"class": "Nx9bqj"},          
                {"class": "a-price-whole"},    
                {"class": "_30jeq3"},          
                {"id": "priceblock_ourprice"}
            ]
            for s in selectors:
                tag = soup.find(None, s)
                if tag:
                    price_text = tag.text
                    clean_price = ''.join(filter(str.isdigit, price_text))
                    return int(clean_price)
        return None
    except:
        return None

# --- UI FIX (No Emojis to avoid TypeError) ---
st.title("Universal Price Tracker")
st.write("Amazon aur Flipkart ke links yahan kaam karenge.")

st.sidebar.header("Settings")
product_url = st.sidebar.text_input("Product Link:")
target_p = st.sidebar.number_input("Target Price (Rs):", value=3000)

if st.sidebar.button("Track Price"):
    if product_url:
        with st.spinner("Wait... Fetching data from cloud..."):
            curr_p = get_live_price(product_url)
            if curr_p:
                st.balloons()
                st.metric("Live Price", f"Rs {curr_p}")
                
                # History
                data_file = "history_v2.json"
                if os.path.exists(data_file):
                    with open(data_file, "r") as f: data = json.load(f)
                else: data = {"history": []}
                
                data["history"].append({"Price": curr_p, "Date": datetime.now().strftime("%d-%m %H:%M")})
                with open(data_file, "w") as f: json.dump(data, f)
                
                df = pd.DataFrame(data["history"])
                st.line_chart(df.set_index("Date"))
            else:
                st.error("Price not found. Check link or API key.")
    else:
        st.warning("Please enter a link.")
