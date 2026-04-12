import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json, os, pandas as pd, plotly.express as px
from datetime import datetime
import time

DATA_FILE = "price_history.json"

st.set_page_config(page_title="Flipkart Tracker Pro", layout="wide")
st.title("🛡️ Smart E-commerce Tracker")

# Cloud-Friendly Scraper
def get_live_price(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless") # Cloud par headless zaruri hai
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Cloud par chromedriver setup
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 20)
        
        # Sahi price tag dhoondna (Flipkart specific)
        price_element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "Nx9bqj")))
        price_text = price_element.text
        driver.quit()
        
        if price_text:
            return int(''.join(filter(str.isdigit, price_text)))
    except Exception as e:
        st.error(f"Scraping Error: {e}")
        driver.quit()
    return None

# UI logic
st.sidebar.header("Settings")
url_input = st.sidebar.text_input("Product Link:")
target_p = st.sidebar.number_input("Target Price (₹):", value=1000)

if st.sidebar.button("Update Price"):
    if url_input:
        with st.spinner('Cloud Engine se price nikal raha hoon...'):
            curr_p = get_live_price(url_input)
            
            if curr_p:
                if os.path.exists(DATA_FILE):
                    with open(DATA_FILE, 'r') as f: data = json.load(f)
                else: data = {"history": [], "low_52": curr_p}

                if curr_p < data.get("low_52", 999999): data["low_52"] = curr_p
                
                data["history"].append({"Price": curr_p, "Date": datetime.now().strftime("%d-%m %H:%M")})
                with open(DATA_FILE, 'w') as f: json.dump(data, f)

                st.balloons()
                c1, c2, c3 = st.columns(3)
                c1.metric("Live Price", f"₹{curr_p}")
                c2.metric("52-Week Low", f"₹{data['low_52']}")
                c3.metric("Target", f"₹{target_p}")

                df = pd.DataFrame(data["history"])
                st.plotly_chart(px.line(df, x="Date", y="Price", title="Price History", markers=True), use_container_width=True)
            else:
                st.error("Price nahi mil paya. Check if link is correct.")

if st.sidebar.button("Clear History"):
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
        st.sidebar.success("History Cleared!")
