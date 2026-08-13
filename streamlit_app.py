"""
SEKWAILA OMEGA X — STREAMLIT LIVE ENGINE
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
from datetime import datetime, timezone
from streamlit_autorefresh import st_autorefresh

from config import (
    ASSETS, DEFAULT_MIN_TF_AGREEMENT, DEFAULT_MIN_SCORE, DEFAULT_MIN_RR,
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, WORKER_POLL_SECONDS,
)
from signals.signal_engine import (
    generate_omega_signal,
    calculate_position_size_for_symbol,
    fetch_usdzar_rate,
    compute_live_correlation_matrix,
    find_order_block,
    grade,
)

st.set_page_config(page_title="SEKWAILA OMEGA X", page_icon="👑", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stApp{background:linear-gradient(135deg,#070b12,#0b111b 55%,#070a10);color:#f4f7fb}
[data-testid="stSidebar"]{background:#080d15}
.omega-title{font-size:2.35rem;font-weight:800;letter-spacing:.03em}
.omega-subtitle{color:#9aa8bb}
.card{background:rgba(17,25,38,.88);border:1px solid #243247;border-radius:14px;padding:15px;min-height:95px}
.label{color:#93a4ba;font-size:.76rem;text-transform:uppercase;letter-spacing:.08em}
.value{font-size:1.4rem;font-weight:750;margin-top:5px}
.buy{color:#34d399}.sell{color:#fb7185}.neutral{color:#fbbf24}
</style>
""", unsafe_allow_html=True)

def num(value, default=0.0):
    try:
        v=float(value)
        return v if pd.notna(v) else default
    except Exception:
        return default

def price(value, decimals=4):
    v=num(value)
    return "—" if v==0 else f"{v:,.{decimals}f}"

def cls(value):
    v=str(value).upper()
    return "buy" if v=="BUY" else "sell" if v=="SELL" else "neutral"

def metric_card(label,value,css=""):
    st.markdown(f'<div class="card"><div class="label">{label}</div><div class="value {css}">{value}</div></div>',unsafe_allow_html=True)

def delta_str(target, entry, decimals=4):
    t,e=num(target),num(entry)
    if t==0 or e==0: return "—"
    d=t-e
    sign="+" if d>=0 else ""
    return f"{sign}{d:,.{decimals}f}"

def score_gauge(score, bias):
    color="#34d399" if bias=="BUY" else "#fb7185" if bias=="SELL" else "#fbbf24"
    fig=go.Figure(go.Indicator(
        mode="gauge+number",
        value=num(score),
        number={"suffix":"","font":{"size":40,"color":color}},
        gauge={
            "axis":{"range":[0,100],"tickcolor":"#4b5a70"},
            "bar":{"color":color,"thickness":0.28},
            "bgcolor":"rgba(0,0,0,0)",
            "borderwidth":0,
            "steps":[
                {"range":[0,50],"color":"#1a2130"},
                {"range":[50,65],"color":"#22293a"},
                {"range":[65,100],"color":"#242e2a"},
            ],
        },
    ))
    fig.update_layout(height=200,margin=dict(l=10,r=10,t=10,b=10),paper_bgcolor="rgba(0,0,0,0)",font={"color":"#f4f7fb"})
    return fig

# ---------------------------------------------------------------------------
# LIVE ALERT SCANNER — sends Telegram alerts while THIS TAB stays open and in
# the foreground. This is NOT a background worker: it only runs on Streamlit
# reruns, which only happen while the browser tab is active. If the screen
# locks or you switch apps, this stops firing until you reopen the tab.
# ---------------------------------------------------------------------------
TELEGRAM_API_URL=f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

def send_telegram_alert(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    try:
        resp=requests.post(TELEGRAM_API_URL,json={"chat_id":TELEGRAM_CHAT_ID,"text":text,"parse_mode":"Markdown"},timeout=10)
        return resp.status_code==200
    except Exception:
        return False

def format_alert_message(res):
    symbol=res["symbol"]; bias=res["bias"]
    icon="🟢 BUY" if bias=="BUY" else "🔴 SELL"
    return "\n".join([
        f"*{icon} — {symbol}*",
        f"Score: {res.get('score')}/100",
        f"Entry: {price(res.get('entry'))}",
        f"Stop: {price(res.get('stop'))}",
        f"TP1: {price(res.get('tp1'))}",
        f"TP2: {price(res.get('tp2'))}",
        f"TP3: {price(res.get('tp3'))}",
        f"R:R: {num(res.get('rr')):.2f}",
        f"Structure: {res.get('structure')}",
    ])

def run_live_alert_scan():
    if "last_alerted_bias" not in st.session_state: st.session_state["last_alerted_bias"]={}
    alerts_sent=[]
    for sym,tkr in ASSETS.items():
        try:
            r=generate_omega_signal(sym,tkr,min_tf=DEFAULT_MIN_TF_AGREEMENT,min_score=DEFAULT_MIN_SCORE,min_rr=DEFAULT_MIN_RR)
        except Exception:
            continue
        if not r.get("ok"): continue
        bias=r.get("bias","NEUTRAL")
        prev=st.session_state["last_alerted_bias"].get(sym)
        if bias in ("BUY","SELL") and bias!=prev:
            if send_telegram_alert(format_alert_message(r)):
                st.session_state["last_alerted_bias"][sym]=bias
                alerts_sent.append(f"{sym} {bias}")
        elif bias=="NEUTRAL" and prev is not None:
            st.session_state["last_alerted_bias"][sym]=None
    st.session_state["last_scan_time"]=datetime.now(timezone.utc)
    st.session_state["last_alerts_sent"]=alerts_sent

symbols=list(ASSETS.keys())
if not symbols:
    st.error("ASSETS is empty. Check config.py."); st.stop()

default_symbol=st.session_state.get("selected_symbol",symbols[0])
if default_symbol not in symbols: default_symbol=symbols[0]

st.sidebar.markdown("## 👑 SEKWAILA OMEGA X")
st.sidebar.caption("LIVE ENGINE")
selected_symbol=st.sidebar.selectbox("Active Asset Focus",symbols,index=symbols.index(default_symbol))
st.session_state.selected_symbol=selected_symbol

account_currency=st.sidebar.selectbox("Account Currency",["ZAR","USD"])
account_balance=st.sidebar.number_input(f"Account Balance ({account_currency})",min_value=0.0,value=10000.0,step=500.0)
risk_pct=st.sidebar.slider("Risk per Trade (%)",0.10,5.00,1.00,0.10)

st.sidebar.markdown("### Engine thresholds")
min_tf=st.sidebar.slider("Minimum TF Agreement",1,4,int(DEFAULT_MIN_TF_AGREEMENT))
min_score=st.sidebar.slider("Minimum Score",0.0,100.0,float(DEFAULT_MIN_SCORE))
min_rr=st.sidebar.number_input("Minimum R:R",0.1,10.0,float(DEFAULT_MIN_RR),0.1)
refresh_seconds=st.sidebar.selectbox("Auto Refresh",[30,60,120,300],index=2)

if st.sidebar.button("🔄 Refresh Now",width="stretch"): st.rerun()
st_autorefresh(interval=refresh_seconds*1000,key="omega_refresh")

st.sidebar.markdown("### 📡 Live Alert Scanner")
telegram_configured=bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
alerts_enabled=st.sidebar.toggle("Telegram alerts (this tab only)",value=telegram_configured,disabled=not telegram_configured)
if not telegram_configured:
    st.sidebar.caption("⚠️ TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set in environment.")
else:
    st.sidebar.caption("⚠️ Only fires while THIS TAB stays open, unlocked, in the foreground. Not a background worker.")

if alerts_enabled and telegram_configured:
    last_scan=st.session_state.get("last_scan_time")
    seconds_since=(datetime.now(timezone.utc)-last_scan).total_seconds() if last_scan else WORKER_POLL_SECONDS+1
    if seconds_since>=WORKER_POLL_SECONDS:
        with st.spinner("Scanning all assets for new signals..."):
            run_live_alert_scan()

st.markdown('<div class="omega-title">👑 SEKWAILA OMEGA X</div><div class="omega-subtitle">LIVE ENGINE — DASHBOARD AND TELEGRAM ALERTS SHARE THE SAME CODE</div>',unsafe_allow_html=True)
st.caption(f"Engine thresholds: {min_tf}/4 TF agreement, {min_score:.1f} min score, {min_rr:.1f} min R:R")
st.warning("⚠️ Informational only. Not financial advice. Score is a rules-based heuristic.")

if alerts_enabled and telegram_configured:
    last_scan=st.session_state.get("last_scan_time")
    sent=st.session_state.get("last_alerts_sent",[])
    if last_scan:
        scan_msg=f"📡 Live scanner active — last full scan {last_scan.strftime('%H:%M:%S UTC')} (every {WORKER_POLL_SECONDS}s while tab is open)"
        if sent: scan_msg+=f" — sent: {', '.join(sent)}"
        st.info(scan_msg)
    else:
        st.info(f"📡 Live scanner active — first scan running now (every {WORKER_POLL_SECONDS}s while tab is open)")

ticker=ASSETS[selected_symbol]
with st.spinner(f"Evaluating {selected_symbol} ({ticker})..."):
    try:
        result=generate_omega_signal(selected_symbol,ticker,min_tf=min_tf,min_score=min_score,min_rr=min_rr)
    except Exception as exc:
        result={"ok":False,"symbol":selected_symbol,"ticker":ticker,"reason":f"{type(exc).__name__}: {exc}"}

if not result.get("ok"):
    st.error(f"Engine could not evaluate {selected_symbol}: {result.get('reason','Unknown error')}")
    if result.get("data_integrity"):
        st.subheader("Data Integrity"); st.json(result["data_integrity"])
    st.stop()

bias=result.get("bias","NEUTRAL")
bull_score=num(result.get("bull_score")); bear_score=num(result.get("bear_score"))
tf_count=len(result.get("tf_biases",{})) or 4
agreement=max(int(result.get("bull_tf_count",0)),int(result.get("bear_tf_count",0)))

st.markdown("## ⚔️ BULL / BEAR SCORE")
c1,c2,c3,c4=st.columns(4)
with c1: metric_card("Bull Score",f"{bull_score:.1f}%","buy")
with c2: metric_card("Bear Score",f"{bear_score:.1f}%","sell")
with c3:
    market_bias="LEAN BULL" if bull_score>bear_score else "LEAN BEAR" if bear_score>bull_score else "NEUTRAL"
    metric_card("Market Bias",market_bias,cls("BUY" if bull_score>bear_score else "SELL" if bear_score>bull_score else "NEUTRAL"))
with c4:
    icon="🟢" if bias=="BUY" else "🔴" if bias=="SELL" else "🟡"
    metric_card("Signal",f"{icon} {bias}",cls(bias))

st.markdown("## 📊 INDICATOR PANEL")
i1,i2,i3,i4=st.columns(4)
with i1:
    metric_card("Price / VWAP",result.get("vwap_status","UNKNOWN")); metric_card("RSI (14)",f"{num(result.get('rsi')):.1f}")
with i2:
    metric_card("MACD Trend",result.get("macd_trend","NEUTRAL")); metric_card("EMA Cross",result.get("ema_cross","NEUTRAL"))
with i3:
    adx=result.get("regime",{}).get("adx",0); metric_card("ADX Power",f"{num(adx):.2f}"); metric_card("ATR 14",price(result.get("atr")))
with i4:
    metric_card("Vol Status",result.get("vol_status","UNKNOWN")); metric_card("Trend Strength","STRONG" if result.get("trend_strong") else "WEAK")

st.markdown("## 📈 MARKET CONTEXT")
r1,r2,r3=st.columns(3)
with r1:
    regime=result.get("regime",{}); st.markdown("### 📈 REGIME"); st.metric("Regime",regime.get("regime","UNKNOWN")); st.write(f"ADX: **{num(regime.get('adx')):.2f}** | Vol Ratio: **{num(regime.get('vol_ratio'),1):.2f}**"); st.caption(result.get("trend_detail",""))
with r2:
    st.markdown("### 🕐 SESSION"); st.metric("Session",result.get("session","UNKNOWN")); st.write(f"Quality: **{num(result.get('session_quality'),50):.1f}%**")
with r3:
    st.markdown("### 💎 PREMIUM / DISCOUNT"); pd_info=result.get("pd_info",{}); st.metric("Zone",result.get("pd_zone","UNKNOWN")); st.write(f"Equilibrium: **{price(pd_info.get('equilibrium'))}**"); st.write(f"Low: {price(pd_info.get('swing_low'))}"); st.write(f"High: {price(pd_info.get('swing_high'))}")

st.markdown("## 💰 POSITION SIZE")
if bias in ("BUY","SELL"):
    sizing_usd=account_balance
    if account_currency=="ZAR":
        usd_zar=fetch_usdzar_rate()
        if usd_zar and usd_zar>0:
            sizing_usd=account_balance/usd_zar
            st.caption(f"Live USD/ZAR: {usd_zar:.4f} | Sizing balance: ${sizing_usd:,.2f}")
        else:
            sizing_usd=0; st.warning("USD/ZAR unavailable; position size withheld.")
    position=calculate_position_size_for_symbol(selected_symbol,sizing_usd,risk_pct,result.get("entry",0),result.get("stop",0))
    if position:
        p1,p2,p3,p4=st.columns(4)
        with p1: st.metric("Risk Amount",f"${position['risk_amount_usd']:,.2f}")
        with p2: st.metric("Stop Distance",price(position["stop_distance"]))
        with p3: st.metric("Lots",f"{position['lots']:.4f}")
        with p4: st.metric("Contract Size",f"{position['contract_size']:g}")
    else: st.info("Position size unavailable.")
else: st.info("No active signal.")

st.markdown(f"## {selected_symbol}")
score_val=num(result.get("score")); letter_grade=grade(score_val)
strength="STRONG " if score_val>=80 else ""

sig_col,gauge_col=st.columns([2,1])
with sig_col:
    if bias=="BUY": st.success(f"📈 {strength}BUY")
    elif bias=="SELL": st.error(f"📉 {strength}SELL")
    else: st.warning("🟡 NEUTRAL / NO SETUP")
    g1,g2=st.columns(2)
    with g1: metric_card("Grade",letter_grade,cls(bias))
    with g2:
        rr=num(result.get("rr")); metric_card("R:R",f"{rr:.2f}" if rr else "—",cls(bias))
    st.caption(f"Timeframe agreement: {agreement}/{tf_count} | Minimum: {min_tf}/{tf_count} | Score threshold: {min_score:.1f}")
    if bias=="NEUTRAL": st.info(result.get("reason") or "No actionable setup.")
with gauge_col:
    st.plotly_chart(score_gauge(score_val,bias),width="stretch",config={"displayModeBar":False})

entry_val=result.get("entry")
q1,q2=st.columns(2)
with q1: st.metric("ENTRY",price(entry_val))
with q2: st.metric("STOP",price(result.get("stop")),delta=delta_str(result.get("stop"),entry_val),delta_color="inverse")

t1,t2,t3=st.columns(3)
with t1: st.metric("TP1",price(result.get("tp1")),delta=delta_str(result.get("tp1"),entry_val))
with t2: st.metric("TP2",price(result.get("tp2")),delta=delta_str(result.get("tp2"),entry_val))
with t3: st.metric("TP3",price(result.get("tp3")),delta=delta_str(result.get("tp3"),entry_val))

st.markdown("## 🧭 MULTI-TIMEFRAME AGREEMENT")
tf_data=result.get("data",{}); tf_biases=result.get("tf_biases",{})
rows=[]
for tf in tf_biases:
    tf_bias=tf_biases.get(tf,"NEUTRAL")
    ob_type="—"
    df_tf=tf_data.get(tf)
    if df_tf is not None and not df_tf.empty and tf_bias in ("BUY","SELL"):
        try:
            ob_t,_,ob_mit,ob_inv=find_order_block(df_tf,tf_bias)
            ob_type="Invalidated" if ob_inv else "Mitigated" if ob_mit else "Active" if ob_t in ("BULLISH_OB","BEARISH_OB") else "—"
        except Exception:
            ob_type="—"
    rows.append({"Timeframe":tf,"Bias":tf_bias,"Structure":result.get("tf_structures",{}).get(tf,"NONE"),"OB":ob_type})
if rows: st.dataframe(pd.DataFrame(rows),width="stretch",hide_index=True)
st.write(f"**Bullish:** {result.get('bull_tf_count',0)}/{tf_count} | **Bearish:** {result.get('bear_tf_count',0)}/{tf_count} | **Required:** {min_tf}/{tf_count}")

st.markdown("## 🧠 SMART MONEY CONCEPTS")
s1,s2=st.columns(2)
with s1:
    st.markdown("### Market Structure"); st.write(f"**{result.get('structure','NONE')}**")
    st.markdown("### Order Block"); st.write(f"**{result.get('ob_type','NONE')}**")
    zone=result.get("ob_zone")
    if zone: st.write(f"Zone: **{price(zone[0])} — {price(zone[1])}**")
    st.write(f"Mitigated: **{'YES' if result.get('ob_mitigated') else 'NO'}**")
    st.write(f"Invalidated: **{'YES' if result.get('ob_invalidated') else 'NO'}**")
with s2:
    st.markdown("### Liquidity Sweep"); st.write("**YES**" if result.get("sweep") else "**NO**"); st.caption(result.get("sweep_detail","NO_SWEEP"))
    st.markdown("### Fair Value Gap"); fvg=result.get("fvg")
    if fvg:
        st.write(f"**{fvg.get('type','UNKNOWN')}**"); zone=fvg.get("zone")
        if zone: st.write(f"Zone: **{price(zone[0])} — {price(zone[1])}**")
        st.write(f"Filled: **{'YES' if fvg.get('filled') else 'NO'}**")
    else: st.write("**NONE / NO UNFILLED FVG**")

with st.expander("📊 Live Asset Correlation"):
    if st.button("Calculate Correlation Matrix",width="stretch"):
        with st.spinner("Fetching correlation data..."):
            try: corr=compute_live_correlation_matrix()
            except Exception as exc: corr=None; st.error(f"Correlation calculation failed: {exc}")
        if corr is not None and not corr.empty: st.dataframe(corr,width="stretch")
        else: st.info("Not enough live data to calculate correlation.")

with st.expander("🛡️ Data Integrity"):
    integrity=result.get("data_integrity",{})
    if integrity:
        st.dataframe(pd.DataFrame([{"Timeframe":tf,"Status":status} for tf,status in integrity.items()]),width="stretch",hide_index=True)
    st.caption("The engine removes the currently forming candle before indicator and structure calculations.")

now=datetime.now(timezone.utc)
st.markdown("---")
st.caption(f"SEKWAILA OMEGA X • {selected_symbol} • {ticker} • {now.strftime('%Y-%m-%d %H:%M:%S UTC')} • Auto-refresh {refresh_seconds}s")
