import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import os
from datetime import datetime
import time

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

# --- SMART SCRAPER LOGIC ---
def get_flipkart_price(url):
    # Pro Headers: Flipkart ko lagega asli browser hai
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.google.com/",
        "Connection": "keep-alive"
    }
    
    try:
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=20)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Flipkart ke alag-alag price tags check karo
            # Nx9bqj sabse naya hai, lekin backup ke liye dusre bhi rakhe hain
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
                price_val = int(''.join(filter(str.isdigit, price_text)))
                return price_val
        return None
    except Exception as e:
        return None

# --- UI DESIGN ---
st.title("💰 Smart Price Tracker")
st.markdown("Flipkart ke products ka price track karein aur target hit hone par alert payein.")

# Sidebar Controls
st.sidebar.header("Settings")
product_url = st.sidebar.text_input("Flipkart Link Yahan Dalein:")
target_price = st.sidebar.number_input("Target Price (₹):", min_value=1, value=3000)

if st.sidebar.button("Update Price"):
    if product_url:
        if "flipkart.com" in product_url:
            with st.spinner("Flipkart se price nikal raha hoon... thoda sabar karein..."):
                current_price = get_flipkart_price(product_url)
                
                if current_price:
                    data = load_data()
                    timestamp = datetime.now().strftime("%d/%m %H:%M")
                    data["history"].append({"Date": timestamp, "Price": current_price})
                    
                    if data["best_price"] is None or current_price < data["best_price"]:
                        data["best_price"] = current_price
                    
                    save_data(data)
                    st.balloons()
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Live Price", f"₹{current_price:,}")
                    col2.metric("Best Price", f"₹{data['best_price']:,}")
                    col3.metric("Your Target", f"₹{target_price:,}")

                    df = pd.DataFrame(data["history"])
                    st.line_chart(df.set_index("Date"))
                    
                    if current_price <= target_price:
                        st.success("🎯 BINGO! Target hit ho gaya!")
                else:
                    st.error("Price nahi mil paya. Flipkart abhi block kar raha hai. Thodi der baad 'Update Price' phir se dabayein.")
        else:
            st.warning("Bhai, sahi link dalo.")
    else:
        st.info("Pehle link dalo.")

if st.sidebar.button("Clear History"):
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
        st.sidebar.success("History deleted!")
        st.rerun()
