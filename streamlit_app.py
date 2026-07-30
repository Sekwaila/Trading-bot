import streamlit as st
import requests
from datetime import datetime

# ==========================
# PAGE SETTINGS
# ==========================

st.set_page_config(
    page_title="Sekwaila Omega X",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Sekwaila Omega X")
st.caption("Institutional Smart Money Trading Assistant")

st.write(datetime.now().strftime("%d %B %Y | %H:%M:%S"))

# ==========================
# API KEY
# ==========================

API_KEY = st.secrets["TWELVEDATA_API_KEY"]

# ==========================
# MARKETS
# ==========================

MARKETS = {
    "XAU/USD": "XAU/USD",
    "BTC/USD": "BTC/USD",
    "EUR/USD": "EUR/USD",
    "US30": "DJI",
    "SP500": "SPX",
    "DXY": "DXY"
}

# ==========================
# LIVE PRICE FUNCTION
# ==========================

def get_price(symbol):

    url = (
        f"https://api.twelvedata.com/price"
        f"?symbol={symbol}"
        f"&apikey={API_KEY}"
    )

    r = requests.get(url).json()

    if "price" in r:
        return float(r["price"])

    return None

# ==========================
# LIVE DASHBOARD
# ==========================

st.header("📊 Live Markets")

cols = st.columns(3)

i = 0

for name, symbol in MARKETS.items():

    price = get_price(symbol)

    with cols[i % 3]:

        if price:
            st.metric(name, f"{price:,.2f}")
        else:
            st.error(f"{name} unavailable")

    i += 1
