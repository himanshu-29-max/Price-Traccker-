import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import json, os, time
from datetime import datetime

st.set_page_config(page_title="Price Tracker Pro", layout="wide")
st.title("💰 Smart Price Tracker")

def get_live_price(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    # Real browser jaisa dikhne ke liye User-Agent
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
    
    chrome_options.binary_location = "/usr/bin/chromium"
    
    try:
        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(url)
        
        # 15 second tak wait karega jab tak price wala element na mil jaye
        wait = WebDriverWait(driver, 15)
        
        # Flipkart ke naye price selectors (Nx9bqj sabse common hai)
        price_element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "Nx9bqj")))
        
        price_text = price_element.text
        driver.quit()
        
        return int(''.join(filter(str.isdigit, price_text)))
    except Exception as e:
        print(f"Error: {e}")
        driver.quit()
        return None

# --- UI ---
url_input = st.sidebar.text_input("Product Link:")
target_p = st.sidebar.number_input("Target Price (₹):", value=1000)

if st.sidebar.button("Update Price"):
    if url_input:
        with st.spinner('Checking price on server... Isme 10-15 seconds lag sakte hain.'):
            curr_p = get_live_price(url_input)
            if curr_p:
                st.balloons()
                st.metric("Live Price", f"₹{curr_p}")
                
                # History data
                data_file = "price_history.json"
                if os.path.exists(data_file):
                    with open(data_file, 'r') as f: data = json.load(f)
                else: data = {"history": []}
                
                data["history"].append({"Price": curr_p, "Date": datetime.now().strftime("%H:%M")})
                with open(data_file, 'w') as f: json.dump(data, f)
                
                df = pd.DataFrame(data["history"])
                st.line_chart(df.set_index("Date"))
            else:
                st.error("Bhai, Flipkart ne block kiya ya link galat hai. Ek baar normal link open karke dekho.")
