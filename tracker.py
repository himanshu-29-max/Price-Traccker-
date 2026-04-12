import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import os
from datetime import datetime

# --- CONFIG ---
DATA_FILE = "price_history.json"

st.set_page_config(page_title="Price Tracker Pro", layout="wide", page_icon="💰")

# --- HEADER ---
st.markdown("<h1 style='text-align: center;'>🛡️ Smart Price Tracker</h1>", unsafe_allow_with_html=True)
st.markdown("---")

# --- SCRAPER ENGINE (Requests Method) ---
def get_live_price(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Flipkart Price Class (Nx9bqj)
            price_tag = soup.find("div", {"class": "Nx9bqj"})
            
            if price_tag:
                # Text se price nikal kar number mein badalna
                price_val = int(''.join(filter(str.isdigit, price_tag.text)))
                return price_val
        return None
    except Exception as e:
        st.error(f"Error: {e}")
        return None

# --- SIDEBAR & UI ---
st.sidebar.header("🔧 Control Panel")
url_input = st.sidebar.text_input("Flipkart Product Link:")
target_p = st.sidebar.number_input("Your Target Price (₹):", value=1000)

if st.sidebar.button("Update Price"):
    if url_input:
        if "flipkart.com" not in url_input:
            st.error("Bhai, sirf Flipkart ka link dalo!")
        else:
            with st.spinner('Fetching Latest Price...'):
                curr_p = get_live_price(url_input)
                
                if curr_p:
                    st.balloons()
                    
                    # History Management
                    if os.path.exists(DATA_FILE):
                        with open(DATA_FILE, 'r') as f: data = json.load(f)
                    else: data = {"history": [], "low": curr_p}

                    if curr_p < data.get("low", 999999): data["low"] = curr_p
                    
                    data["history"].append({"Price": curr_p, "Date": datetime.now().strftime("%d-%m %H:%M")})
                    
                    with open(DATA_FILE, 'w') as f: json.dump(data, f)

                    # Display Metrics
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Live Price", f"₹{curr_p:,}")
                    c2.metric("Best Price", f"₹{data['low']:,}")
                    c3.metric("Target", f"₹{target_p:,}")

                    # Chart
                    df = pd.DataFrame(data["history"])
                    st.line_chart(df.set_index("Date"))
                    
                    if curr_p <= target_p:
                        st.success("🎯 Target Hit! Price gir gaya hai, ab kharid lo!")
                else:
                    st.error("Price nahi mil paya. Flipkart abhi block kar raha hai, thodi der baad try karo.")
    else:
        st.warning("Pehle link toh dalo bhai!")

if st.sidebar.button("Clear History"):
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
        st.sidebar.success("History Cleared!")
