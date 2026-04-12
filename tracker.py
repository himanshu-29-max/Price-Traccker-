import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import altair as alt # Graph ke liye Altair import kiya
import json, os, re
from datetime import datetime

# --- CONFIG ---
SCRAPER_API_KEY = "98140924c53c3da8de89d24bccc92568" 

st.set_page_config(page_title="Price Master Pro", layout="wide")

def get_live_price(url):
    proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}&render=true&wait=5000"
    
    try:
        response = requests.get(proxy_url, timeout=120)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            
            # 1. Flipkar ka MAIN PRICE tag (Accuracy ke liye)
            main_price_tag = soup.find("div", {"class": "Nx9bqj C6R3Y2"})
            if not main_price_tag:
                main_price_tag = soup.find("div", {"class": "Nx9bqj"})
            
            if main_price_tag:
                # Text se number nikalna
                val = re.sub(r'[^\d]', '', main_price_tag.text)
                if val: return int(val)
            
            # 2. Amazon backup
            amazon_price = soup.find("span", {"class": "a-price-whole"})
            if amazon_price:
                return int(''.join(filter(str.isdigit, amazon_price.text)))

        return None
    except Exception as e:
        return None

# --- UI (Bina Emojis ke) ---
st.title("Universal Price Tracker")
st.write("Bilkul professional price history graph dekhein.")

# Sidebar
st.sidebar.header("Settings")
product_url = st.sidebar.text_input("Product Link:")
target_p = st.sidebar.number_input("Target Price (Rs):", value=3000)

if st.sidebar.button("Track Price"):
    if product_url:
        if "http" not in product_url:
            st.error("Bhai, poora link dalo (https://...)")
        else:
            with st.spinner("Real price fetch ho raha hai cloud se..."):
                curr_p = get_live_price(product_url)
                
                if curr_p:
                    st.balloons()
                    st.success(f"Verified Price: Rs {curr_p:,}")
                    
                    # Display Metrics
                    c1, c2 = st.columns(2)
                    c1.metric("Live Price", f"Rs {curr_p:,}")
                    c2.metric("Target Price", f"Rs {target_p:,}")

                    # History Management
                    log_file = "pro_log.json"
                    if os.path.exists(log_file):
                        with open(log_file, "r") as f: data = json.load(f)
                    else: data = {"history": []}
                    
                    # Store as object with timestamp
                    data["history"].append({"Price": curr_p, "Date": datetime.now()})
                    with open(log_file, "w") as f: json.dump(data, f, default=str)
                    
                    # --- PROFESSIONAL GRAPH LOGIC (Altair Area Chart) ---
                    df = pd.DataFrame(data["history"])
                    # Convert 'Date' column back to datetime object
                    df['Date'] = pd.to_datetime(df['Date'])
                    
                    if not df.empty:
                        # Area Chart banaya
                        area_chart = alt.Chart(df).mark_area(
                            color='lightblue', # Pichle screenshot ki tarah light blue color
                            opacity=0.7,       # Thodi transparency
                            interpolate='monotone' # Smooth lines
                        ).encode(
                            x=alt.X('Date:T', axis=alt.Axis(format="%Y-%m-%d")), # X-axis par dates
                            y=alt.Y('Price:Q', title="Price (Rs)"), # Y-axis par price
                            tooltip=['Date:T', 'Price:Q'] # Hover karne par data dikhe
                        ).properties(
                            title='Price History over Time', # Graph ka title
                            width='container', # Full width use kare
                            height=400          # Graph ki height
                        )
                        
                        # Graph ke upar exact points (dots) add kiye
                        line_points = alt.Chart(df).mark_point(
                            color='darkblue', size=100 # Dots ka color aur size
                        ).encode(
                            x='Date:T', y='Price:Q'
                        )
                        
                        # Dono ko merge kar diya
                        final_chart = area_chart + line_points
                        
                        # Altair chart ko display kiya
                        st.altair_chart(final_chart, use_container_width=True)
                    
                else:
                    st.error("Price fetch nahi ho paya. Ek baar link check karein.")
    else:
        st.warning("Pehle complete link toh dalo!")

if st.sidebar.button("Reset History"):
    if os.path.exists("pro_log.json"):
        os.remove("pro_log.json")
        st.sidebar.success("History deleted!")
        st.rerun()
