import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from twilio.rest import Client
import smtplib
from pymongo import MongoClient
import time

# --- CONFIGURATION (Yahan apni details bharo) ---
MONGO_URL = "TUMHARA_MONGODB_CONNECTION_LINK"
TWILIO_SID = "TUMHARA_TWILIO_SID"
TWILIO_TOKEN = "TUMHARA_TWILIO_TOKEN"
FROM_WHATSAPP = "whatsapp:+14155238886" # Twilio Sandbox Number
TO_WHATSAPP = "whatsapp:+91TUMHARA_NUMBER"
MY_EMAIL = "TUMHARA_GMAIL"
EMAIL_PASS = "TUMHARA_APP_PASSWORD"

# --- DATABASE CONNECT ---
client = MongoClient(MONGO_URL)
db = client['PriceTracker']
collection = db['products']

# --- ALERT FUNCTIONS ---
def send_alerts(prod_name, price, link):
    # 1. WhatsApp Alert
    twilio_client = Client(TWILIO_SID, TWILIO_TOKEN)
    twilio_client.messages.create(
        from_=FROM_WHATSAPP,
        body=f"📉 PRICE DROP! \n{prod_name} is now ₹{price}\nLink: {link}",
        to=TO_WHATSAPP
    )
    
    # 2. Email Alert
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login(MY_EMAIL, EMAIL_PASS)
    msg = f"Subject: Price Drop Alert!\n\n{prod_name} dropped to {price}. Buy now: {link}"
    server.send_mail(MY_EMAIL, MY_EMAIL, msg)
    server.quit()

# --- SCRAPER ENGINE ---
def get_price(url):
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    try:
        driver.get(url)
        time.sleep(10)
        price_tag = driver.find_element(By.CLASS_NAME, "Nx9bqj")
        p = int(''.join(filter(str.isdigit, price_tag.text)))
        driver.quit()
        return p
    except:
        driver.quit()
        return None

# --- UI ---
st.title("🛡️ Buyhatke Clone (Pro Edition)")
url = st.sidebar.text_input("Product Link:")
target = st.sidebar.number_input("Target Price:", value=1000)

if st.sidebar.button("Start Tracking"):
    while True:
        current_p = get_price(url)
        if current_p:
            st.write(f"Current Price: ₹{current_p} (Checking again in 1 hour...)")
            # Database mein update karo
            collection.update_one({"url": url}, {"$set": {"price": current_p}}, upsert=True)
            
            if current_p <= target:
                st.success("Target Hit! Sending Alerts...")
                send_alerts("Product", current_p, url)
                break # Alert bhej kar ruk jayega
        
        time.sleep(3600) 