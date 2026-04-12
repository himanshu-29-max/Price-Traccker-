import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import pandas as pd
import json, os, time
from datetime import datetime

# --- CONFIG ---
DATA_FILE = "price_history.json"

st.set_page_config(page_title="Price Tracker", layout="wide")
st.title("💰 Smart Price Tracker")

# Cloud-Friendly Scraper
def get_live_price(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get(url)
        time.sleep(5)
        
        # Flipkart price selector
        price_element = driver.find_element(By.CLASS_NAME, "Nx9bqj")
        price_text = price_element.text
        driver.quit()
        
        return int(''.join(filter(str.isdigit, price_text)))
    except Exception as e:
        return None

# UI Sidebar
url_input = st.sidebar.text_input("Product Link:")
target_p = st.sidebar.number_input("Target Price:", value=1000)

if st.sidebar.button("Update Price"):
    if url_input:
        with st.spinner('Checking...'):
            curr_p = get_live_price(url_input)
            if curr_p:
                st.metric("Live Price", f"₹{curr_p}")
                # History Save Logic
                if os.path.exists(DATA_FILE):
                    with open(DATA_FILE, 'r') as f: data = json.load(f)
                else: data = {"history": []}
                
                data["history"].append({"Price": curr_p, "Date": datetime.now().strftime("%H:%M")})
                with open(DATA_FILE, 'w') as f: json.dump(data, f)
                
                df = pd.DataFrame(data["history"])
                st.line_chart(df.set_index("Date"))
            else:
                st.error("Could not fetch price. Check link.")
