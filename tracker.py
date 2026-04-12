import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json, os, re
from datetime import datetime

# --- CONFIG ---
SCRAPER_API_KEY = "98140924c53c3da8de89d24bccc92568" 

st.set_page_config(page_title="Price Master Pro", layout="wide")

def get_live_price(url):
    # &render=true ke saath bypass=true add kiya hai fresh data ke liye
    proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}&render=true&wait=5000"
    
    try:
        response = requests.get(proxy_url, timeout=120)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            
            # 1. Flipkar ka MAIN PRICE tag (Ye sabse accurate hai)
            # Flipkart often uses these specific classes for the large price
            main_price = soup.find("div", {"class": "Nx9bqj C6R3Y2"})
            if not main_price:
                main_price = soup.find("div", {"class": "Nx9bqj"})
            
            if main_price:
                # Sirf digits nikalna
                val = re.sub(r'[^\d]', '', main_price.text)
                if val: return int(val)
            
            # 2. Backup: Agar upar wala fail hua toh is hidden tag ko dhoondo
            script_tag = soup.find("script", {"id": "jsonLD"})
            if script_tag:
                try:
                    data = json.loads(script_tag.string)
                    # JSON data se price nikalna sabse safe hota hai
                    return int(float(data[0]['offers']['price']))
                except: pass

        return None
    except Exception as e:
        return None

# --- UI ---
st.title("Universal Price Tracker")
st.write("Real-time price tracking without errors.")

st.sidebar.header("Settings")
product_url = st.sidebar.text_input("Product Link:")
target_p = st.sidebar.number_input("Target Price (Rs):", value=12000) # Baseline set to 12k

if st.sidebar.button("Track Price"):
    if product_url:
        with st.spinner("Bypassing cache and fetching real price..."):
            curr_p = get_live_price(product_url)
            
            if curr_p:
                st.balloons()
                st.success(f"Verified Price: Rs {curr_p:,}")
                
                # Metric
                st.metric("Live Price", f"Rs {curr_p:,}")

                # History logic
                log_file = "fresh_log.json"
                if os.path.exists(log_file):
                    with open(log_file, "r") as f: data = json.load(f)
                else: data = {"history": []}
                
                data["history"].append({"Price": curr_p, "Date": datetime.now().strftime("%H:%M:%S")})
                with open(log_file, "w") as f: json.dump(data, f)
                
                df = pd.DataFrame(data["history"])
                st.line_chart(df.set_index("Date"))
            else:
                st.error("Price not found. Ek baar complete URL dalkar try karein.")
    else:
        st.warning("Link dalo bhai!")

if st.sidebar.button("Clear History"):
    if os.path.exists("fresh_log.json"):
        os.remove("fresh_log.json")
        st.rerun()
