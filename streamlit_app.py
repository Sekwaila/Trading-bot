import streamlit as st
import requests
from signal_engine import generate_omega_signal, format_telegram_message, fetch_usdzar_rate

# ==========================================
# 1. PAGE CONFIG & DARK TERMINAL STYLING
# ==========================================
st.set_page_config(
    page_title="SEKWAILA OMEGA X",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    /* Dark Terminal Background */
    .stApp {
        background-color: #0d1117;
        color: #e6edf3;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Live Broker Banner */
    .broker-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 15px;
        text-align: center;
    }
    .price-value {
        font-size: 36px;
        font-weight: 900;
        color: #2ea043;
    }
    .price-label {
        font-size: 11px;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }

    /* Signal Headers */
    .extreme-sell { color: #f85149; font-weight: 900; font-size: 26px; }
    .extreme-buy { color: #2ea043; font-weight: 900; font-size: 26px; }
    .neutral-signal { color: #e3b341; font-weight: 800; font-size: 24px; }

    /* Hide standard Streamlit chrome */
    header { visibility: hidden; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CONTROL PANEL & MANUAL PRICE SYNC
# ==========================================
st.markdown("## 👑 **SEKWAILA OMEGA X**")
st.caption("SINGLE SOURCE OF TRUTH · MANUAL SIGNAL ENGINE")

col_symbol, col_tf = st.columns(2)
with col_symbol:
    symbol = st.selectbox("Market Pair", ["XAUUSDm", "BTCUSDm", "US30m", "EURUSDm"], index=0)
with col_tf:
    timeframe = st.selectbox("Primary Timeframe", ["15m", "1h", "4h"], index=0)

col_acc, col_override = st.columns(2)
with col_acc:
    acc_zar = st.number_input("Account Balance (ZAR)", value=500.0, step=50.0)
with col_override:
    # Direct broker sync input to eliminate price mismatch
    manual_price = st.number_input(
        f"📲 MT4 Live Price Sync ({symbol})", 
        value=4331.09 if "XAU" in symbol else 65000.00, 
        step=0.01,
        format="%.2f"
    )

# Telegram Secret Credentials
telegram_token = st.secrets.get("TELEGRAM_BOT_TOKEN", None)
telegram_chat_id = st.secrets.get("TELEGRAM_CHAT_ID", None)

# ==========================================
# 3. GENERATE OMEGA SIGNAL DATA
# ==========================================
sig = generate_omega_signal(
    symbol=symbol,
    manual_price_override=manual_price,
    metaapi_token=st.secrets.get("META_API_TOKEN", None),
    account_id=st.secrets.get("META_API_ACCOUNT_ID", None)
)

if not sig.get("ok", False):
    st.error(f"Error computing engine signal: {sig.get('reason')}")
    st.stop()

# Live Price Display Card
st.markdown(f"""
<div class="broker-card">
    <div class="price-label">LIVE BROKER REFERENCE PRICE ({sig['symbol']})</div>
    <div class="price-value">{sig['entry']:,.2f}</div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 4. SIGNAL BANNER & METRICS
# ==========================================
title = sig["signal_title"]
if "SELL" in title:
    st.markdown(f"<div class='extreme-sell'>🔥 {title} — {sig['symbol']}</div>", unsafe_allow_html=True)
elif "BUY" in title:
    st.markdown(f"<div class='extreme-buy'>🚀 {title} — {sig['symbol']}</div>", unsafe_allow_html=True)
else:
    st.markdown(f"<div class='neutral-signal'>🟡 {title} — {sig['symbol']}</div>", unsafe_allow_html=True)

# Top Metrics Row
m1, m2, m3, m4 = st.columns(4)
m1.metric("Score", f"{sig['score']}/100")
m2.metric("TF Agreement", sig["tf_agreement"])
m3.metric("R:R Ratio", f"1:{sig['rr']}")
m4.metric("Market Bias", sig["bias"])

st.markdown("---")

# Execution Targets (Only shown for non-neutral setups)
if title != "NEUTRAL":
    st.markdown("### 🎯 **REFERENCE LEVELS (MANUAL EXECUTION ONLY)**")
    e_col, sl_col, tp1_col, tp2_col, tp3_col = st.columns(5)
    e_col.metric("Entry Ref", f"{sig['entry']:,.2f}")
    sl_col.metric("Stop Loss (SL)", f"{sig['stop']:,.2f}")
    tp1_col.metric("Take Profit 1", f"{sig['tp1']:,.2f}")
    tp2_col.metric("Take Profit 2", f"{sig['tp2']:,.2f}")
    tp3_col.metric("Take Profit 3", f"{sig['tp3']:,.2f}")
    st.markdown("---")

# Technicals & Smart Money Concepts (SMC) Breakdown
st.markdown("### 📊 **TECHNICAL ANALYSIS & SMC STRUCTURE**")
t1, t2 = st.columns(2)

with t1:
    st.markdown("#### **Indicators**")
    st.write(f"• **RSI:** `{sig['rsi']}`")
    st.write(f"• **MACD:** `{sig['macd_trend']}`")
    st.write(f"• **EMA Cross:** `{sig['ema_cross']}`")
    st.write(f"• **ADX:** `{sig['adx']}`")

with t2:
    st.markdown("#### **Market Structure (SMC)**")
    st.write(f"• **Structure:** `{sig['structure']}`")
    st.write(f"• **Liquidity:** `{sig['liquidity']}`")
    st.write(f"• **Fair Value Gap:** `{sig['fvg']}`")
    st.write(f"• **Order Block:** `{sig['ob_type']}`")

st.warning("⚠️ SIGNAL ONLY — NO AUTO TRADE. ALL POSITIONS MUST BE ENTERED MANUALLY ON MT4/MT5.")

# ==========================================
# 5. TELEGRAM PUSH ACTION
# ==========================================
if st.button("📲 Push Signal to Telegram Channel", use_container_width=True):
    if not telegram_token or not telegram_chat_id:
        st.error("Telegram credentials missing! Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in secrets.toml")
    else:
        telegram_text = format_telegram_message(sig)
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        payload = {
            "chat_id": telegram_chat_id,
            "text": telegram_text,
            "parse_mode": "Markdown"
        }
        res = requests.post(url, json=payload, timeout=5)
        if res.status_code == 200:
            st.success("Signal successfully pushed to Telegram!")
        else:
            st.error(f"Failed to send Telegram alert. Status Code: {res.status_code}")
