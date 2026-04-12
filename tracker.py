import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json, os, re
from datetime import datetime

# --- CONFIG ---
# ScraperAPI Key quotes mein honi chahiye
SCRAPER_API_KEY = "98140924c53c3da8de89d24bccc92568" 

st.set_page_config(page_title="Universal Price Tracker", layout="wide")

def get_live_price(url):
    # render=true aur wait=10000 taaki JavaScript poori tarah load ho aur asli price dikhe
    proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}&render=true&wait=10000"
    
    try:
        response = requests.get(proxy_url, timeout=120)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            
            # 1. Sabse pehle Flipkart ka exact Big Price class dhoondo
            # Yeh class sirf main product price ke liye hoti hai
            main_price_tag = soup.find("div", {"class": "Nx9bqj C6R3Y2"})
            if not main_price_tag:
                main_price_tag = soup.find("div", {"class": "Nx9bqj"})
            
            if main_price_tag:
                price_val = int(''.join(filter(str.isdigit, main_price_tag.text)))
                return price_val
            
            # 2. Amazon Backup (Agar Amazon ka link ho)
            amazon_price = soup.find("span", {"class": "a-price-whole"})
            if amazon_price:
                return int(''.join(filter(str.isdigit, amazon_price.text)))

            # 3. Last Option: Pure page mein '₹' ke baad wale numbers dhoondo aur sabse bada uthao
            page_text = soup.get_text()
            regex_prices = re.findall(r'₹\s?([0-9,]+)', page_text)
            if regex_prices:
                prices = [int(p.replace(',', '')) for p in regex_prices]
                # Filter taaki chote delivery charges ya discount amounts skip ho jayein
                valid_prices = [p for p in prices if p > 500] 
                if valid_prices:
                    return max(valid_prices) # Sabse bada price hi main price hota hai
                        
        return None
    except Exception as e:
        return None

# --- UI INTERFACE ---
st.markdown("<h1 style='text-align: center;'>🌐 Universal Price Tracker</h1>", unsafe_allow_with_html=True)
st.write("Amazon aur Flipkart ke products ka accurate price track karein.")

# Sidebar
st.sidebar.header("🔧 Control Panel")
product_url = st.sidebar.text_input("Product Link (Complete URL):")
target_p = st.sidebar.number_input("Target Price (Rs):", value=3000)

if st.sidebar.button("Track Price"):
    if product_url:
        if "http" not in product_url:
            st.error("Bhai, poora link dalo (https://...)")
        else:
            with st.spinner("Bypass Engine price nikal raha hai... 40-50 seconds lag sakte hain..."):
                curr_p = get_live_price(product_url)
                
                if curr_p:
                    st.balloons()
                    st.success(f"Success! Current Price mil gaya: Rs {curr_p:,}")
                    
                    # Display Metrics
                    c1, c2 = st.columns(2)
                    c1.metric("Live Price", f"Rs {curr_p:,}")
                    c2.metric("Target Price", f"Rs {target_p:,}")

                    # History Management
                    data_file = "price_log.json"
                    if os.path.exists(data_file):
                        with open(data_file, "r") as f: data = json.load(f)
                    else: data = {"history": []}
                    
                    data["history"].append({"Price": curr_p, "Date": datetime.now().strftime("%d-%m %H:%M")})
                    with open(data_file, "w") as f: json.dump(data, f)
                    
                    # Graph
                    df = pd.DataFrame(data["history"])
                    st.line_chart(df.set_index("Date"))
                    
                    if curr_p <= target_p:
                        st.warning("🔥 Deal Alert! Price aapke target se niche hai!")
                else:
                    st.error("Price fetch nahi ho paya. Ek baar link check karo ki poora page khul raha hai na?")
    else:
        st.warning("Pehle product ka link dalo bhai!")

if st.sidebar.button("Reset History"):
    if os.path.exists("price_log.json"):
        os.remove("price_log.json")
        st.sidebar.success("History deleted!")
        st.rerun()
