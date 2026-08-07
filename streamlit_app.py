import datetime
import plotly.graph_objects as go
import streamlit as st

from config import config
from data.market_data import fetch_institutional_data, fetch_usdzar_rate, compute_live_correlation_matrix
from signals.signal_engine import run_quantitative_smc_engine
from trade_manager import calculate_position_size

st.set_page_config(
    page_title="SEKWAILA OMEGA X Pro Engine",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Inter:wght@300;400;600&display=swap');
    .stApp { background-color: #0c0a07; color: #e5d5b7; font-family: 'Inter', sans-serif; }
    .title-cinzel { font-family: 'Cinzel', serif; color: #dfb15b; letter-spacing: 2px; }
    .css-card { background-color: #14100b; border: 1px solid #3b2d18; border-radius: 8px; padding: 14px; margin-bottom: 12px; }
    .signal-box-buy { background: linear-gradient(180deg, #0d1a0e 0%, #060d07 100%); border: 1px solid #00e676; border-radius: 10px; padding: 20px; }
    .signal-box-sell { background: linear-gradient(180deg, #1f0b0b 0%, #0a0404 100%); border: 1px solid #ff5252; border-radius: 10px; padding: 20px; }
    .signal-box-blocked { background: linear-gradient(180deg, #211c12 0%, #0c0a07 100%); border: 1px solid #ffb74d; border-radius: 10px; padding: 20px; }
    .signal-box-danger { background: linear-gradient(180deg, #2a0505 0%, #0c0a07 100%); border: 1px solid #ff1744; border-radius: 10px; padding: 20px; }
    .text-gold { color: #dfb15b !important; }
    .text-green { color: #00e676 !important; font-weight: bold; }
    .text-red { color: #ff5252 !important; font-weight: bold; }
    .text-orange { color: #ffb74d !important; font-weight: bold; }
</style>
""",
    unsafe_allow_html=True,
)

tf_data, data_integrity = fetch_institutional_data(config.SYMBOL)
results = run_quantitative_smc_engine(tf_data, data_integrity)
corr_matrix = compute_live_correlation_matrix()

with st.sidebar:
    st.markdown("### 💰 Position Sizing")
    account_balance_zar = st.number_input("Account Balance (ZAR)", min_value=0.0, value=config.ACCOUNT_BALANCE_ZAR_DEFAULT, step=500.0)
    risk_pct_input = st.number_input("Risk per Trade (%)", min_value=0.1, max_value=10.0, value=config.RISK_PERCENT_DEFAULT, step=0.1)

usdzar_rate = fetch_usdzar_rate()
account_balance_usd = (account_balance_zar / usdzar_rate) if usdzar_rate else None

head_c1, head_c2, head_c3 = st.columns([1.2, 2.5, 1.2])
with head_c1:
    st.markdown("<h3 class='title-cinzel' style='margin:0;'>👑 SEKWAILA OMEGA X</h3>", unsafe_allow_html=True)
with head_c2:
    st.markdown("<h2 style='text-align: center; margin:0;' class='title-cinzel'>SEKWAILA OMEGA X — QUANT ENGINE</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #dfb15b; font-size: 11px; margin:0;'>PRO-GRADE ALGORITHMIC SMC EXECUTION</p>", unsafe_allow_html=True)
with head_c3:
    now_sast = (datetime.datetime.utcnow() + datetime.timedelta(hours=2)).strftime("%H:%M:%S")
    st.markdown(f"<div style='text-align: right;'><b class='text-gold'>{now_sast} SAST</b><br/><small style='color: #888;'>PROD_SESSION_ACTIVE</small></div>", unsafe_allow_html=True)

st.markdown("---")

if not results["data_ok"]:
    missing_list = "".join(f"<li>{tf}: {data_integrity[tf]}</li>" for tf in results["missing_timeframes"])
    st.markdown(f'<div class="signal-box-danger"><h2 class="title-cinzel" style="color:#ff1744; margin:0;">⚠ DATA FEED DOWN</h2><ul style="font-size:11px; color:#ff5252;">{missing_list}</ul></div>', unsafe_allow_html=True)
    st.stop()

col_left, col_center, col_right = st.columns([1.1, 2.4, 1.2])

with col_left:
    st.markdown(f'<div class="css-card"><small class="text-gold">📈 MARKET REGIME & QUALITY</small><h4 style="color: #00e676; margin: 4px 0;">{results["regime"]["regime"]}</h4><div style="font-size:11px; color:#aaa; margin-top:6px;"><div>ADX (14, Wilder): <b>{results["regime"]["adx"]}</b></div><div>Volatility Ratio: <b>{results["regime"]["vol_ratio"]}</b></div><div>Slope Angle: <b>{results["regime"]["angle"]}°</b></div></div></div>', unsafe_allow_html=True)
    
    filter_status_class = "text-green" if results["passed_filters"] else "text-red"
    filter_text = "APPROVED FOR EXECUTION" if results["passed_filters"] else "BLOCKED BY SAFETY BARRIER"
    rejection_html = "".join(f"<li style='color:#ff5252;'>{r}</li>" for r in results["filter_rejections"]) or "<li style='color:#00e676;'>All Safety Checks Passed</li>"
    
    st.markdown(f'<div class="css-card"><small class="text-gold">🛡️ EXECUTION BARRIER</small><br/><span class="{filter_status_class}" style="font-size:11px;">{filter_text}</span><ul style="font-size:10px; margin-top:6px; padding-left:14px;">{rejection_html}</ul></div>', unsafe_allow_html=True)
    
    pos_size = calculate_position_size(account_balance_usd, risk_pct_input, results["entry"], results["stop_loss"]) if results["bias"] in ("BUY", "SELL") else None
    
    if usdzar_rate is None:
        st.markdown('<div class="css-card"><small class="text-gold">💰 POSITION SIZE</small><div style="font-size:10px; color:#ff5252; margin-top:6px;">USDZAR feed unavailable — cannot convert ZAR.</div></div>', unsafe_allow_html=True)
    elif pos_size is None:
        st.markdown('<div class="css-card"><small class="text-gold">💰 POSITION SIZE</small><div style="font-size:10px; color:#aaa; margin-top:6px;">No active BUY/SELL signal to size.</div></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="css-card"><small class="text-gold">💰 POSITION SIZE</small><div style="font-size:11px; margin-top:6px;"><div>Balance: <b class="text-gold">R{account_balance_zar:,.0f}</b> (${account_balance_usd:,.2f})</div><div>Suggested Size: <b class="text-green">{pos_size["lots"]} lots</b></div></div></div>', unsafe_allow_html=True)

with col_center:
    box_class = "signal-box-buy" if results["bias"] == "BUY" and results["passed_filters"] else ("signal-box-sell" if results["bias"] == "SELL" and results["passed_filters"] else "signal-box-blocked")
    bias_display = f"CONFIRMED {results['bias']} ↑" if results["bias"] == "BUY" and results["passed_filters"] else (f"CONFIRMED {results['bias']} ↓" if results["bias"] == "SELL" and results["passed_filters"] else "NEUTRAL / NO SETUP")
    bias_color = "text-green" if "BUY" in bias_display else ("text-red" if "SELL" in bias_display else "text-gold")

    st.markdown(f'<div class="{box_class}"><div style="display: flex; justify-content: space-between;"><div><h2 style="margin:0; color: #fff;" class="title-cinzel">{config.DISPLAY_SYMBOL}</h2></div><div style="text-align: right;"><small style="color: #aaa;">CONFLUENCE</small><h2 style="margin:0;" class="text-gold">{results["probability"]}%</h2></div></div><hr style="border-color: #3b2d18; margin: 10px 0;"/><h1 class="{bias_color}" style="margin: 2px 0; font-family: \'Cinzel\', serif;">{bias_display}</h1><br/><div style="display: flex; justify-content: space-around; text-align: center;"><div><small style="color: #888;">ENTRY</small><br/><b>{results["entry"]:.2f}</b></div><div><small style="color: #888;">TP1</small><br/><b class="text-green">{results["tp1"]:.2f}</b></div><div><small style="color: #888;">TP2</small><br/><b class="text-green">{results["tp2"]:.2f}</b></div><div><small style="color: #888;">STOP LOSS</small><br/><b class="text-red">{results["stop_loss"]:.2f}</b></div></div></div>', unsafe_allow_html=True)

    df_chart = results["df_15m"]
    fig = go.Figure(data=[go.Candlestick(x=df_chart.index, open=df_chart["Open"], high=df_chart["High"], low=df_chart["Low"], close=df_chart["Close"], increasing_line_color="#00e676", decreasing_line_color="#ff5252")])
    fig.update_layout(template="plotly_dark", paper_bgcolor="#14100b", plot_bgcolor="#14100b", height=320, margin=dict(l=10, r=10, t=35, b=10), xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.markdown(f'<div class="css-card"><small class="text-gold">💡 KATLEGO AI REASONING</small><p style="font-size: 11px; color: #ccc; margin-top: 6px; line-height:1.4;">{results["ai_narrative"]}</p></div>', unsafe_allow_html=True)
    if corr_matrix is not None:
        st.dataframe(corr_matrix.style.background_gradient(cmap="coolwarm", axis=None), use_container_width=True)
