import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json, os, re
from datetime import datetime

# --- CONFIG ---
SCRAPER_API_KEY = "98140924c53c3da8de89d24bccc92568" 

st.set_page_config(page_title="Price Master", layout="wide")

def get_live_price(url):
    # render=true is important for Flipkart's dynamic price loading
    proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}&render=true&wait=10000"
    
    try:
        response = requests.get(proxy_url, timeout=120)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            
            # 1. SPECIFIC SELECTORS: Flipkart ka main price hamesha in classes mein hota hai
            # Inhe priority di gayi hai
            main_tags = [
                "div.Nx9bqj.C6R3Y2", 
                "div.Nx9bqj", 
                "span.a-price-whole" # Amazon backup
            ]
            
            for selector in main_tags:
                tag = soup.select_one(selector)
                if tag:
                    # Sirf numbers nikalna
                    price_str = re.sub(r'[^\d]', '', tag.text)
                    if price_str:
                        return int(price_str)
            
            # 2. BACKUP: Agar class nahi mili toh pure HTML mein dhoondo
            # Lekin wahi number uthao jo 1000 se bada ho (taaki delivery charges skip ho jayein)
            page_text = soup.get_text()
            all_prices = re.findall(r'₹\s?([0-9,]+)', page_text)
            if all_prices:
                numeric_prices = [int(p.replace(',', '')) for p in all_prices]
                # Flipkart par main price aksar sabse bada hota hai exchange price se
                return max(numeric_prices)
                        
        return None
    except:
        return None

# --- UI ---
st.title("Universal Price Tracker")
st.write("Bilkul accurate price check karne ke liye 'Track Price' dabayein.")

st.sidebar.header("Control Panel")
product_url = st.sidebar.text_input("Product Link:")
target_p = st.sidebar.number_input("Target Price (Rs):", value=3000)

if st.sidebar.button("Track Price"):
    if product_url:
        with st.spinner("Checking real price on Flipkart..."):
            curr_p = get_live_price(product_url)
            
            if curr_p:
                st.balloons()
                st.success(f"Original Price Mil Gaya: Rs {curr_p:,}")
                
                # Metric
                st.metric("Current Price", f"Rs {curr_p:,}", delta_color="inverse")

                # History Logic
                data_file = "final_price_log.json"
                if os.path.exists(data_file):
                    with open(data_file, "r") as f: data = json.load(f)
                else: data = {"history": []}
                
                data["history"].append({"Price": curr_p, "Date": datetime.now().strftime("%d-%m %H:%M")})
                with open(data_file, "w") as f: json.dump(data, f)
                
                df = pd.DataFrame(data["history"])
                st.line_chart(df.set_index("Date"))
            else:
                st.error("Price nahi mil paya. Link check karein.")
    else:
        st.warning("Link dalo bhai!")
