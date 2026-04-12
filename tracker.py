import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json, os
from datetime import datetime

# --- CONFIG ---
# Check kar lena ki key quotes "" ke andar hi ho
SCRAPER_API_KEY = "98140924c53c3da8de89d24bccc92568" 

st.set_page_config(page_title="Price Tracker Pro", layout="wide")
st.title("🛡️ Smart Tracker (Ultimate Mode)")

def get_live_price(url):
    # Proxy URL: Flipkart ko chakma dene ke liye
    proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}"
    
    try:
        response = requests.get(proxy_url, timeout=60)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Flipkart ke 3 alag-alag price tags (ek na ek kaam karega)
            selectors = [
                {"class": "Nx9bqj"}, 
                {"class": "Nx9bqj C6R3Y2"}, 
                {"class": "_30jeq3 _16Jk6d"}
            ]
            
            price_text = None
            for s in selectors:
                tag = soup.find("div", s)
                if tag:
                    price_text = tag.text
                    break
            
            if price_text:
                # Text se number nikalna (e.g., ₹1,499 -> 1499)
                return int(''.join(filter(str.isdigit, price_text)))
        return None
    except Exception as e:
        return None

# --- UI LOGIC ---
st.sidebar.header("Settings")
product_url = st.sidebar.text_input("Flipkart Link Yahan Dalein:")
target_price = st.sidebar.number_input("Target Price (₹):", value=3000)

if st.sidebar.button("Update Price"):
    if product_url:
        with st.spinner("Proxy Engine bypass kar raha hai... balloons tayyar rakho..."):
            current_price = get_live_price(product_url)
            
            if current_price:
                st.balloons()
                st.metric("Live Price", f"₹{current_price:,}")
                st.success(f"Bhai Price mil gaya! Current Price ₹{current_price} hai.")
                
                # History File logic
                data_file = "history.json"
                if os.path.exists(data_file):
                    with open(data_file, "r") as f: data = json.load(f)
                else: data = {"history": []}
                
                data["history"].append({"Price": current_price, "Date": datetime.now().strftime("%H:%M")})
                with open(data_file, "w") as f: json.dump(data, f)
                
                df = pd.DataFrame(data["history"])
                st.line_chart(df.set_index("Date"))
            else:
                st.error("Bhai abhi bhi block hai. Ek baar check karo link browser mein khul raha hai na?")
    else:
        st.warning("Pehle link dalo!")
