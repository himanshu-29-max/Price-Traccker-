import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import os

# --- CLOUD-OPTIMIZED SCRAPER ---
def get_live_price(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    # Streamlit Cloud par Chrome ka path set karna
    chrome_options.binary_location = "/usr/bin/chromium"
    
    try:
        # Service setup bina webdriver-manager ke (Cloud handles it via packages.txt)
        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        driver.get(url)
        st.write("Page load ho gaya...") # Debugging ke liye
        
        # Price nikalo
        price_tag = driver.find_element(By.CLASS_NAME, "Nx9bqj")
        p = int(''.join(filter(str.isdigit, price_tag.text)))
        
        driver.quit()
        return p
    except Exception as e:
        st.error(f"Error detail: {e}")
        return None

# Baki ka UI code (Update Price button etc.) waisa hi rahega
