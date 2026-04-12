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
    # &render=true ke saath &wait=5000 (5 sec) add kiya hai taaki page poora load ho
    proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}&render=true&wait=5000"
    
    try:
        response = requests.get(proxy_url, timeout=120)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Saare possible price tags (Flipkart, Amazon aur general)
            selectors = [
                {"class": "Nx9bqj"},          # Flipkart New
                {"class": "Nx9bqj C6R3Y2"},   # Flipkart Variant
                {"class": "a-price-whole"},    # Amazon
                {"class": "_30jeq3"},          # Flipkart Old
                {"id": "priceblock_ourprice"}, # Amazon Old
                {"class": "price"}             # General
            ]
            
            for s in selectors:
                tag = soup.find(None, s)
                if tag:
                    price_text = tag.text
                    # Sirf digits nikalna
                    clean_price = ''.join(filter(str.isdigit, price_text))
                    if clean_price:
                        return int(clean_price)
        return None
    except Exception as e:
        return None

# --- UI ---
st.title("Universal Price Tracker")
st.write("Amazon aur Flipkart ke links yahan kaam karenge.")

st.sidebar.header("Settings")
product_url = st.sidebar.text_input("Product Link:")
target_p = st.sidebar.number_input("Target Price (Rs):", value=3000)

if st.sidebar.button("Track Price"):
    if product_url:
        with st.spinner("Proxy Engine bypass kar raha hai... isme 40-50 seconds lag sakte hain..."):
            curr_p = get_live_price(product_url)
            if curr_p:
                st.balloons()
                st.metric("Live Price", f"Rs {curr_p:,}")
                st.success(f"Bhai Price mil gaya! Current: Rs {curr_p}")
                
                # History Save
                data_file = "history_v3.json"
                if os.path.exists(data_file):
                    with open(data_file, "r") as f: data = json.load(f)
                else: data = {"history": []}
                
                data["history"].append({"Price": curr_p, "Date": datetime.now().strftime("%d-%m %H:%M")})
                with open(data_file, "w") as f: json.dump(data, f)
                
                df = pd.DataFrame(data["history"])
                st.line_chart(df.set_index("Date"))
            else:
                st.error("Price fetch nahi ho paya. Ek baar link browser mein check karo ya API key dashboard check karo.")
    else:
        st.warning("Pehle link dalo!")
