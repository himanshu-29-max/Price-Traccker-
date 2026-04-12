import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import altair as alt
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
            # Sabse accurate price tags
            main_tag = soup.find("div", {"class": "Nx9bqj C6R3Y2"}) or soup.find("div", {"class": "Nx9bqj"})
            if main_tag:
                return int(re.sub(r'[^\d]', '', main_tag.text))
        return None
    except:
        return None

# --- UI ---
st.title("Universal Price Tracker")
st.write("Professional Price History Graph (Buyhatke Style)")

# Sidebar
st.sidebar.header("Settings")
product_url = st.sidebar.text_input("Product Link:")
target_p = st.sidebar.number_input("Target Price (Rs):", value=3000)

if st.sidebar.button("Track Price"):
    if product_url:
        with st.spinner("Bypassing security and loading professional graph..."):
            curr_p = get_live_price(product_url)
            
            if curr_p:
                st.balloons()
                st.metric("Current Price", f"Rs {curr_p:,}")
                
                # Data Management
                log_file = "history_pro.json"
                if os.path.exists(log_file):
                    with open(log_file, "r") as f: data = json.load(f)
                else: data = {"history": []}
                
                data["history"].append({"Price": curr_p, "Time": datetime.now().isoformat()})
                with open(log_file, "w") as f: json.dump(data, f)
                
                # --- PROFESSIONAL AREA CHART (Altair) ---
                df = pd.DataFrame(data["history"])
                df['Time'] = pd.to_datetime(df['Time'])
                
                # Area chart with gradient effect
                area = alt.Chart(df).mark_area(
                    line={'color':'#FF4B4B'},
                    color=alt.Gradient(
                        gradient='linear',
                        stops=[alt.GradientStop(color='white', offset=0),
                               alt.GradientStop(color='#FF4B4B', offset=1)],
                        x1=1, x2=1, y1=1, y2=0
                    ),
                    interpolate='monotone',
                    opacity=0.4
                ).encode(
                    x=alt.X('Time:T', title='Time'),
                    y=alt.Y('Price:Q', title='Price (Rs)', scale=alt.Scale(zero=False))
                )

                # Add points/dots
                points = alt.Chart(df).mark_point(filled=True, size=60, color='#FF4B4B').encode(
                    x='Time:T',
                    y='Price:Q'
                )

                final_chart = (area + points).properties(height=400).interactive()
                st.altair_chart(final_chart, use_container_width=True)
                
            else:
                st.error("Price fetch nahi ho paya. Ek baar complete product link check karein.")
    else:
        st.warning("Pehle product ka link dalo!")

if st.sidebar.button("Reset History"):
    if os.path.exists("history_pro.json"):
        os.remove("history_pro.json")
        st.sidebar.success("History deleted!")
        st.rerun()
