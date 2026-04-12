import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import pandas as pd
import json, os, time
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Price Tracker", layout="wide")
st.title("💰 Smart Price Tracker")

# Cloud-Specific Scraper
def get_live_price(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Ye do line Streamlit Cloud par Chrome chalane ke liye sabse zaruri hain
    chrome_options.binary_location = "/usr/bin/chromium"
    service = Service("/usr/bin/chromedriver")
    
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(url)
        time.sleep(7) # Cloud thoda slow ho sakta hai, isliye 7 sec wait
        
        # Flipkart price selector
        price_element = driver.find_element(By.CLASS_NAME, "Nx9bqj")
        price_text = price_element.text
        driver.quit()
        
        return int(''.join(filter(str.isdigit, price_text)))
    except Exception as e:
        print(f"Error: {e}")
        return None

# --- UI ---
url_input = st.sidebar.text_input("Product Link:")
target_p = st.sidebar.number_input("Target Price (₹):", value=1000)

if st.sidebar.button("Update Price"):
    if url_input:
        with st.spinner('Checking price on cloud server...'):
            curr_p = get_live_price(url_input)
            if curr_p:
                st.balloons()
                st.metric("Live Price", f"₹{curr_p}")
                
                # Simple History Management
                data_file = "price_history.json"
                if os.path.exists(data_file):
                    with open(data_file, 'r') as f: data = json.load(f)
                else: data = {"history": []}
                
                data["history"].append({"Price": curr_p, "Date": datetime.now().strftime("%H:%M")})
                with open(data_file, 'w') as f: json.dump(data, f)
                
                df = pd.DataFrame(data["history"])
                st.line_chart(df.set_index("Date"))
            else:
                st.error("Price fetch nahi ho paya. Ek baar check karo link sahi hai na?")
