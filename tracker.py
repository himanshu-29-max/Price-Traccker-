import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json, os, re
from datetime import datetime

# --- CONFIG ---
# ScraperAPI Key quotes mein honi chahiye
SCRAPER_API_KEY = "98140924c53c3da8de89d24bccc92568" 

st.set_page_config(page_title="Price Tracker", layout="wide")

def get_live_price(url):
    # render=true aur wait=10000 taaki JavaScript load ho aur asli price dikhe
    proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}&render=true&wait=10000"
    
    try:
        response = requests.get(proxy_url, timeout=120)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            
            # 1. Sabse pehle Flipkart ka main price tag dhoondo
            main_price_tag = soup.find("div", {"class": "Nx9bqj C6R3Y2"})
            if not main_price_tag:
                main_price_tag = soup.find("div", {"class": "Nx9bqj"})
            
            if main_price_tag:
                return int(''.join(filter(str.isdigit, main_price_tag.text)))
            
            # 2. Amazon ka main price tag
            amazon_price = soup.find("span", {"class": "a-price-whole"})
            if amazon_price:
                return int(''.join(filter(str.isdigit, amazon_price.text)))

            # 3. Backup Plan: Pure page mein sabse bada price dhoondo
            page_text = soup.get_text()
            regex_prices = re.findall(r'₹\s?([0-9,]+)', page_text)
            if regex_prices:
                prices = [int(p.replace(',', '')) for p in regex_prices]
                valid_prices = [p for p in prices if p > 500] 
                if valid_prices:
                    return max(valid_prices)
                        
        return None
    except:
        return None

# --- UI (Bina Emojis ke taaki error na aaye) ---
st.title("Universal Price Tracker")
st.write("Amazon aur Flipkart ke links yahan track karein.")

# Sidebar
st.sidebar.header("Control Panel")
product_url = st.sidebar.text_input("Product Link:")
target_p = st.sidebar.number_input("Target Price (Rs):", value=3000)

if st.sidebar.button("Track Price"):
    if product_url:
        with st.spinner("Fetching data from cloud..."):
            curr_p = get_live_price(product_url)
            
            if curr_p:
                st.balloons()
                st.success(f"Price mil gaya: Rs {curr_p}")
                
                # Metrics
                c1, c2 = st.columns(2)
                c1.metric("Live Price", f"Rs {curr_p:,}")
                c2.metric("Target Price", f"Rs {target_p:,}")

                # History
                data_file = "price_log.json"
                if os.path.exists(data_file):
                    with open(data_file, "r") as f: data = json.load(f)
                else: data = {"history": []}
                
                data["history"].append({"Price": curr_p, "Date": datetime.now().strftime("%d-%m %H:%M")})
                with open(data_file, "w") as f: json.dump(data, f)
                
                df = pd.DataFrame(data["history"])
                st.line_chart(df.set_index("Date"))
            else:
                st.error("Price fetch nahi ho paya. Ek baar link check karo.")
    else:
        st.warning("Pehle link dalo!")

if st.sidebar.button("Reset History"):
    if os.path.exists("price_log.json"):
        os.remove("price_log.json")
        st.sidebar.success("History deleted!")
        st.rerun()
