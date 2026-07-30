import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(
    page_title="Sekwaila Omega X",
    page_icon="📈",
    layout="wide"
)

st.markdown("""
<style>

html,body,[class*="css"]{
background:#0E1117;
color:white;
}

.block-container{
padding-top:1rem;
}

.metric{
background:#161B22;
padding:15px;
border-radius:12px;
}

hr{
border:1px solid #222;
}

</style>
""",unsafe_allow_html=True)

st.title("📈 SEKWAILA OMEGA X")
st.caption("Institutional Smart Money Trading Assistant")

st.write(
datetime.now().strftime(
"%d %B %Y | %H:%M:%S"
)
)

# ======================================
# SIDEBAR
# ======================================

st.sidebar.title("⚙️ CONTROL PANEL")

ACCOUNT=st.sidebar.number_input(
"Account Balance",
100,
1000000,
1000
)

RISK=st.sidebar.slider(
"Risk %",
0.5,
5.0,
1.0
)

TIMEFRAME=st.sidebar.selectbox(
"Timeframe",
[
"M5",
"M15",
"M30",
"H1",
"H4",
"D1"
]
)

AUTO_REFRESH=st.sidebar.checkbox(
"Auto Refresh",
True
)

st.sidebar.success("OMEGA X ONLINE")

# ======================================
# DXY
# ======================================

st.header("🧭 DXY COMPASS")

d1,d2,d3,d4=st.columns(4)

d1.metric(
"Trend",
"WAIT"
)

d2.metric(
"Bias",
"Neutral"
)

d3.metric(
"Strength",
"0%"
)

d4.metric(
"Session",
"Waiting"
)

st.divider()

# ======================================
# WATCHLIST
# ======================================

MARKETS=[
"XAUUSD",
"BTCUSD",
"EURUSD",
"US30",
"SP500"
]

for market in MARKETS:

    st.subheader(market)

    a,b,c,d,e,f=st.columns(6)

    a.metric(
    "Signal",
    "WAIT"
    )

    b.metric(
    "Confidence",
    "0%"
    )

    c.metric(
    "Entry",
    "--"
    )

    d.metric(
    "SL",
    "--"
    )

    e.metric(
    "TP",
    "--"
    )

    f.metric(
    "Trend",
    "--"
    )

    fig=go.Figure()

    fig.update_layout(

    template="plotly_dark",

    height=250,

    margin=dict(
    l=0,
    r=0,
    t=20,
    b=0
    ),

    xaxis_title="",

    yaxis_title=""

    )

    st.plotly_chart(
    fig,
    use_container_width=True
    )

    st.divider()

# ======================================
# SIGNAL HISTORY
# ======================================

st.header("📜 SIGNAL HISTORY")

history=pd.DataFrame({

"Time":[],

"Market":[],

"Signal":[],

"Entry":[],

"SL":[],

"TP":[],

"Confidence":[]

})

st.dataframe(
history,
use_container_width=True,
hide_index=True
)

st.divider()

st.success("Omega X Engine Loaded")
# ======================================================
# PART 2 - OMEGA X ANALYSIS ENGINE
# ======================================================

import numpy as np

# ----------------------------
# DEMO MARKET DATA
# (Will be replaced with live data)
# ----------------------------

def get_market_data(symbol):

    np.random.seed(abs(hash(symbol)) % 1000)

    price = np.cumsum(np.random.randn(300)) + 100

    df = pd.DataFrame()

    df["Open"] = price
    df["High"] = price + np.random.rand(300)
    df["Low"] = price - np.random.rand(300)
    df["Close"] = price + np.random.randn(300)*0.2

    return df


# ----------------------------
# TREND ENGINE
# ----------------------------

def trend(df):

    sma20 = df.Close.rolling(20).mean()

    sma50 = df.Close.rolling(50).mean()

    if sma20.iloc[-1] > sma50.iloc[-1]:
        return "Bullish"

    elif sma20.iloc[-1] < sma50.iloc[-1]:
        return "Bearish"

    return "Neutral"


# ----------------------------
# BOS
# ----------------------------

def bos(df):

    recent_high = df.High.tail(20).max()

    if df.Close.iloc[-1] > recent_high:

        return True

    return False


# ----------------------------
# CHOCH
# ----------------------------

def choch(df):

    last = df.Close.tail(10)

    if last.iloc[-1] > last.mean():

        return True

    return False


# ----------------------------
# MSS
# ----------------------------

def mss(df):

    last = df.Close.tail(5)

    if last.is_monotonic_increasing:

        return True

    if last.is_monotonic_decreasing:

        return True

    return False


# ----------------------------
# FAIR VALUE GAP
# ----------------------------

def fvg(df):

    gap = abs(df.High.iloc[-2]-df.Low.iloc[-1])

    return gap > df.Close.std()


# ----------------------------
# ORDER BLOCK
# ----------------------------

def order_block(df):

    candle = df.iloc[-2]

    if candle.Close > candle.Open:

        return "Bullish"

    return "Bearish"


# ----------------------------
# LIQUIDITY SWEEP
# ----------------------------

def liquidity(df):

    high = df.High.tail(15).max()

    low = df.Low.tail(15).min()

    close = df.Close.iloc[-1]

    if close > high:

        return "Buy Side"

    elif close < low:

        return "Sell Side"

    return "None"


# ----------------------------
# AI CONFIDENCE
# ----------------------------

def confidence(df):

    score = 0

    if bos(df):
        score += 20

    if choch(df):
        score += 20

    if mss(df):
        score += 15

    if fvg(df):
        score += 15

    if order_block(df) == "Bullish":
        score += 15

    if liquidity(df) != "None":
        score += 15

    return min(score,100)


# ----------------------------
# SIGNAL
# ----------------------------

def signal(df):

    score = confidence(df)

    t = trend(df)

    if score >= 80 and t=="Bullish":

        return "BUY"

    elif score >=80 and t=="Bearish":

        return "SELL"

    return "WAIT"
