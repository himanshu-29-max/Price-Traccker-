import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import os
from datetime import datetime

# --- APP CONFIG ---
st.set_page_config(page_title="Price Master", layout="wide")

# --- DATA STORAGE ---
DATA_FILE = "price_history.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"history": [], "best_price": None}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# --- SCRAPER LOGIC ---
def get_flipkart_price(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            # Flipkart Price Tag
            price_box = soup.find("div", {"class": "Nx9bqj"})
            if price_box:
                price_text = price_box.text.replace("₹", "").replace(",", "")
                return int(float(price_text))
        return None
    except Exception as e:
        return None

# --- UI DESIGN ---
st.title("💰 Smart Price Tracker")
st.markdown("Flipkart ke products ka price track karein aur target hit hone par alert payein.")

# Sidebar Controls
st.sidebar.header("Settings")
product_url = st.sidebar.text_input("Flipkart Link Yahan Dalein:")
target_price = st.sidebar.number_input("Target Price (₹):", min_value=1, value=1000)

if st.sidebar.button("Update Price"):
    if product_url:
        if "flipkart.com" in product_url:
            with st.spinner("Checking price..."):
                current_price = get_flipkart_price(product_url)
                
                if current_price:
                    data = load_data()
                    
                    # History Update
                    timestamp = datetime.now().strftime("%d/%m %H:%M")
                    data["history"].append({"Date": timestamp, "Price": current_price})
                    
                    # Best Price Logic
                    if data["best_price"] is None or current_price < data["best_price"]:
                        data["best_price"] = current_price
                    
                    save_data(data)

                    # Display Results
                    st.balloons()
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Live Price", f"₹{current_price:,}")
                    col2.metric("All-Time Best", f"₹{data['best_price']:,}")
                    col3.metric("Your Target", f"₹{target_price:,}")

                    # Chart
                    df = pd.DataFrame(data["history"])
                    st.line_chart(df.set_index("Date"))

                    if current_price <= target_price:
                        st.success("🎯 BINGO! Target hit ho gaya. Kharid lo!")
                else:
                    st.error("Price nahi mil paya. Ho sakta hai Flipkart ne block kiya ho, thodi der baad try karein.")
        else:
            st.warning("Bhai, sirf Flipkart links hi kaam karenge.")
    else:
        st.info("Pehle product ka link copy-paste karo.")

if st.sidebar.button("Clear History"):
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
        st.sidebar.success("History deleted!")
        st.rerun()
