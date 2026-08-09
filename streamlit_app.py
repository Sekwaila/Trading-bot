"""
SEKWAILA OMEGA X — DASHBOARD (streamlit_app.py — matches your Procfile's web entry)

Every page here calls generate_omega_signal() from engine.py — the exact
same function worker.py calls for Telegram alerts. The dashboard and your
phone can never show different numbers for the same asset.
"""
import datetime
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from config import ASSETS, DEFAULT_MIN_TF_AGREEMENT, DEFAULT_MIN_SCORE, DEFAULT_MIN_RR
from engine import generate_omega_signal, grade, fetch_usdzar_rate, compute_live_correlation_matrix, calculate_position_size
import database

st.set_page_config(page_title="SEKWAILA OMEGA X", page_icon="👑", layout="wide", initial_sidebar_state="collapsed")

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
    .text-gold { color: #dfb15b !important; }
    .text-green { color: #00e676 !important; font-weight: bold; }
    .text-red { color: #ff5252 !important; font-weight: bold; }
    .text-orange { color: #ffb74d !important; font-weight: bold; }
</style>
""",
    unsafe_allow_html=True,
)

database.init_db()


@st.cache_data(ttl=60)
def cached_signal(symbol, ticker, min_tf, min_score, min_rr):
    return generate_omega_signal(symbol, ticker, min_tf, min_score, min_rr)


with st.sidebar:
    st.markdown("<h2 class='title-cinzel'>👑 SEKWAILA</h2>", unsafe_allow_html=True)
    st.markdown("<small style='color:#888;'>OMEGA X — LIVE ENGINE</small>", unsafe_allow_html=True)
    st.markdown("---")
    page = st.radio("MODULE", ["Dashboard", "Market Scanner", "Heatmap", "AI Narrator",
                                "Multi-Timeframe", "Correlation Matrix", "Trade Journal",
                                "Performance", "Settings"], index=0)
    st.markdown("---")
    account_zar = st.number_input("Account (ZAR)", min_value=100.0, value=1000.0, step=100.0)
    risk_pct = st.slider("Risk per Trade (%)", 0.1, 5.0, 1.0, 0.1)
    st.markdown("---")
    st.caption(f"Engine thresholds: {DEFAULT_MIN_TF_AGREEMENT}/4 TF agreement, {DEFAULT_MIN_SCORE} min score, {DEFAULT_MIN_RR} min R:R — set in config.py")
    if st.button("🔄 Refresh All Data"):
        st.cache_data.clear()
        st.rerun()
    st.caption("⚠️ Informational only. Not financial advice. Score is a rules-based heuristic, not a backtested win rate.")

usdzar_rate = fetch_usdzar_rate()
account_balance_usd = (account_zar / usdzar_rate) if usdzar_rate else None

st.markdown("<h1 class='title-cinzel' style='text-align:center; margin:0;'>SEKWAILA OMEGA X</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#dfb15b; font-size:11px; letter-spacing:2px;'>LIVE ENGINE — DASHBOARD AND TELEGRAM ALERTS SHARE THE SAME CODE</p>", unsafe_allow_html=True)
st.markdown("---")


def render_data_down(res):
    st.markdown(
        f"""<div class="signal-box-blocked"><h3 class="title-cinzel" style="color:#ff5252;">⚠ DATA UNAVAILABLE — {res.get('symbol','')}</h3>
        <p style="font-size:12px; color:#ccc;">{res.get('reason','Unknown error')}</p></div>""",
        unsafe_allow_html=True,
    )


if page == "Dashboard":
    asset_choice = st.selectbox("Active Asset Focus", list(ASSETS.keys()), index=0)
    res = cached_signal(asset_choice, ASSETS[asset_choice], DEFAULT_MIN_TF_AGREEMENT, DEFAULT_MIN_SCORE, DEFAULT_MIN_RR)

    if not res["ok"]:
        render_data_down(res)
        st.stop()

    col_left, col_center, col_right = st.columns([1.1, 2.4, 1.2])

    with col_left:
        bull_pct = res["bull_score"]
        bear_pct = res["bear_score"]
        market_bias_label = "STRONG BULL" if bull_pct - bear_pct >= 25 else ("STRONG BEAR" if bear_pct - bull_pct >= 25 else ("LEAN BULL" if bull_pct > bear_pct else ("LEAN BEAR" if bear_pct > bull_pct else "NEUTRAL")))
        market_bias_color = "#00e676" if "BULL" in market_bias_label else ("#ff5252" if "BEAR" in market_bias_label else "#dfb15b")
        st.markdown(
            f"""<div class="css-card">
            <small class="text-gold">⚔️ BULL / BEAR SCORE</small>
            <div style="margin-top:6px;">
                <div style="display:flex; justify-content:space-between; font-size:11px;"><span>BULL SCORE</span><b class="text-green">{bull_pct}%</b></div>
                <div style="background:#2a2214; border-radius:4px; height:8px; margin-bottom:6px;"><div style="background:#00e676; width:{bull_pct}%; height:8px; border-radius:4px;"></div></div>
                <div style="display:flex; justify-content:space-between; font-size:11px;"><span>BEAR SCORE</span><b class="text-red">{bear_pct}%</b></div>
                <div style="background:#2a2214; border-radius:4px; height:8px;"><div style="background:#ff5252; width:{bear_pct}%; height:8px; border-radius:4px;"></div></div>
            </div>
            <div style="margin-top:10px; text-align:center; padding:6px; border-radius:6px; background:#0c0a07; border:1px solid {market_bias_color};">
                <small style="color:#888;">MARKET BIAS</small><br/>
                <b style="color:{market_bias_color}; font-size:13px;">{market_bias_label}</b>
            </div>
            </div>""",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""<div class="css-card">
            <small class="text-gold">📊 INDICATOR PANEL</small>
            <div style="font-size:11px; margin-top:6px; line-height:1.9;">
                <div style="display:flex; justify-content:space-between;"><span style="color:#aaa;">Price/VWAP</span><b style="color:{'#00e676' if res['vwap_status']=='ABOVE' else '#ff5252'};">{res['vwap_status']}</b></div>
                <div style="display:flex; justify-content:space-between;"><span style="color:#aaa;">RSI (14)</span><b>{res['rsi']:.1f}</b></div>
                <div style="display:flex; justify-content:space-between;"><span style="color:#aaa;">MACD Trend</span><b style="color:{'#00e676' if res['macd_trend']=='BULLISH' else '#ff5252'};">{res['macd_trend']}</b></div>
                <div style="display:flex; justify-content:space-between;"><span style="color:#aaa;">ADX Power</span><b>{res['regime']['adx']}</b></div>
                <div style="display:flex; justify-content:space-between;"><span style="color:#aaa;">EMA Cross</span><b style="color:{'#00e676' if res['ema_cross']=='BULLISH' else '#ff5252'};">{res['ema_cross']}</b></div>
                <div style="display:flex; justify-content:space-between;"><span style="color:#aaa;">ATR 14</span><b>{res['atr']:.2f}</b></div>
                <div style="display:flex; justify-content:space-between;"><span style="color:#aaa;">Vol Status</span><b>{res['vol_status']}</b></div>
                <div style="display:flex; justify-content:space-between;"><span style="color:#aaa;">Trend Strength</span><b style="color:{'#00e676' if res['trend_strong'] else '#ffb74d'};">{'STRONG' if res['trend_strong'] else 'WEAK'}</b></div>
                <div style="display:flex; justify-content:space-between;"><span style="color:#aaa;">Status</span><b class="text-gold">{res['bias'] if res['bias'] != 'NEUTRAL' else 'WAIT'}</b></div>
            </div>
            </div>""",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""<div class="css-card"><small class="text-gold">📈 REGIME</small>
            <h4 style="color:#00e676; margin:4px 0;">{res['regime']['regime']}</h4>
            <div style="font-size:11px; color:#aaa;">ADX: <b>{res['regime']['adx']}</b> | Vol Ratio: <b>{res['regime']['vol_ratio']}</b></div></div>""",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""<div class="css-card"><small class="text-gold">🕐 SESSION</small>
            <div style="font-size:12px; margin-top:4px;">{res['session']}</div>
            <div style="font-size:10px; color:#aaa;">Quality: {res['session_quality']}%</div></div>""",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""<div class="css-card"><small class="text-gold">💎 PREMIUM/DISCOUNT</small>
            <div style="font-size:12px; margin-top:4px;">{res['pd_zone']}</div>
            <div style="font-size:10px; color:#aaa;">Equilibrium: {res['pd_info']['equilibrium']:.4f}</div></div>""",
            unsafe_allow_html=True,
        )
        pos_size = calculate_position_size(account_balance_usd, risk_pct, res["entry"], res["stop"]) if res["bias"] in ("BUY", "SELL") else None
        if usdzar_rate is None:
            st.markdown('<div class="css-card"><small class="text-gold">💰 POSITION SIZE</small><div style="font-size:10px; color:#ff5252;">USDZAR feed unavailable.</div></div>', unsafe_allow_html=True)
        elif pos_size is None:
            st.markdown('<div class="css-card"><small class="text-gold">💰 POSITION SIZE</small><div style="font-size:10px; color:#aaa;">No active signal.</div></div>', unsafe_allow_html=True)
        else:
            st.markdown(
                f"""<div class="css-card"><small class="text-gold">💰 POSITION SIZE</small>
                <div style="font-size:11px; margin-top:6px;">
                <div>Risk: <b class="text-gold">R{account_zar * risk_pct / 100:,.2f}</b></div>
                <div>SL Distance: <b>{pos_size['stop_distance']:.2f}</b></div>
                <div>Size: <b class="text-green">{pos_size['lots']} lots</b></div></div></div>""",
                unsafe_allow_html=True,
            )

    with col_center:
        if res["bias"] == "BUY":
            box_class, bias_display, bias_color = "signal-box-buy", "CONFIRMED BUY ↑", "text-green"
        elif res["bias"] == "SELL":
            box_class, bias_display, bias_color = "signal-box-sell", "CONFIRMED SELL ↓", "text-red"
        else:
            box_class, bias_display, bias_color = "signal-box-blocked", "NEUTRAL / NO SETUP", "text-gold"

        reason_html = f"<p style='font-size:10px; color:#ffb74d; margin-top:4px;'>{res['reason']}</p>" if res.get("reason") else ""

        st.markdown(
            f"""<div class="{box_class}">
            <div style="display:flex; justify-content:space-between;">
                <div><h2 style="margin:0; color:#fff;" class="title-cinzel">{res['symbol']}</h2>
                <small style="color:#aaa;">SCORE-BASED SIGNAL (RULES-BASED, NOT BACKTESTED)</small></div>
                <div style="text-align:right;"><small style="color:#aaa;">SCORE</small>
                <h2 style="margin:0;" class="text-gold">{res['score']}/100 ({grade(res['score'])})</h2></div>
            </div>
            <hr style="border-color:#3b2d18; margin:10px 0;"/>
            <h1 class="{bias_color}" style="margin:2px 0; font-family:'Cinzel',serif;">{bias_display}</h1>
            {reason_html}
            <br/>
            <div style="display:flex; justify-content:space-around; text-align:center;">
                <div><small style="color:#888;">ENTRY</small><br/><b>{res['entry']:.4f}</b></div>
                <div><small style="color:#888;">TP1</small><br/><b class="text-green">{res['tp1']:.4f}</b></div>
                <div><small style="color:#888;">TP2</small><br/><b class="text-green">{res['tp2']:.4f}</b></div>
                <div><small style="color:#888;">TP3</small><br/><b class="text-green">{res['tp3']:.4f}</b></div>
                <div><small style="color:#888;">STOP</small><br/><b class="text-red">{res['stop']:.4f}</b></div>
            </div>
            <div style="text-align:center; margin-top:8px; font-size:11px; color:#aaa;">R:R (to TP2): {res['rr']:.2f}</div>
            </div>""",
            unsafe_allow_html=True,
        )
        st.markdown("<br/>", unsafe_allow_html=True)
        df_chart = res["data"]["15M"]
        fig = go.Figure(data=[go.Candlestick(
            x=df_chart.index, open=df_chart["Open"], high=df_chart["High"], low=df_chart["Low"], close=df_chart["Close"],
            increasing_line_color="#00e676", decreasing_line_color="#ff5252",
        )])
        ob_min, ob_max = res["ob_zone"]
        ob_color = "rgba(0,230,118,0.15)" if "BULLISH" in res["ob_type"] else "rgba(255,82,82,0.15)"
        ob_state = "INVALIDATED" if res["ob_invalidated"] else ("MITIGATED" if res["ob_mitigated"] else "UNMITIGATED")
        fig.add_hrect(y0=ob_min, y1=ob_max, fillcolor=ob_color, line_width=1, annotation_text=f"{res['ob_type']} ({ob_state})", annotation_position="bottom left")
        if res["fvg"] is not None:
            fz = res["fvg"]["zone"]
            fig.add_hrect(y0=fz[0], y1=fz[1], fillcolor="rgba(223,177,91,0.18)", line_width=1, line_dash="dot",
                          annotation_text=f"{res['fvg']['type']} (unfilled)", annotation_position="top left")

        # Premium / Discount zone shading, Khansaab-style: upper half of the
        # recent range shaded red (premium — favors selling), lower half
        # shaded blue (discount — favors buying), split by the equilibrium line.
        eq = res["pd_info"]["equilibrium"]
        swing_hi = res["pd_info"]["swing_high"]
        swing_lo = res["pd_info"]["swing_low"]
        fig.add_hrect(y0=eq, y1=swing_hi, fillcolor="rgba(255,82,82,0.08)", line_width=0)
        fig.add_hrect(y0=swing_lo, y1=eq, fillcolor="rgba(66,133,244,0.08)", line_width=0)
        fig.add_hline(y=eq, line_width=1, line_dash="dash", line_color="rgba(223,177,91,0.6)", annotation_text="Equilibrium")

        # Equal-highs / equal-lows liquidity pools
        for eqh in res["eq_highs"][-3:]:
            fig.add_hline(y=eqh, line_width=1, line_dash="dot", line_color="rgba(255,82,82,0.55)", annotation_text="EQH", annotation_position="top right")
        for eql in res["eq_lows"][-3:]:
            fig.add_hline(y=eql, line_width=1, line_dash="dot", line_color="rgba(0,230,118,0.55)", annotation_text="EQL", annotation_position="bottom right")

        # BOS / CHoCH label near the current price, matching the on-chart
        # text style in the Khansaab indicator screenshot.
        struct_label = res["structure"].replace("_WEAK", " (weak)")
        fig.add_annotation(
            x=df_chart.index[-1], y=res["entry"], text=struct_label, showarrow=True, arrowhead=2,
            font=dict(color="#dfb15b", size=11), bgcolor="rgba(12,10,7,0.85)", bordercolor="#3b2d18",
        )

        fig.update_layout(template="plotly_dark", paper_bgcolor="#14100b", plot_bgcolor="#14100b", height=420,
                          margin=dict(l=10, r=10, t=10, b=10), xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.markdown(
            f"""<div class="css-card"><small class="text-gold">💡 REASONING</small>
            <p style="font-size:11px; color:#ccc; margin-top:6px; line-height:1.4;">
            Structure: {res['structure']}. {res['sweep_detail']}. Order block is {ob_state} {res['ob_type']}.
            Trend strength: {res['trend_detail'] if res['trend_strong'] else 'not confirmed'}.
            Zone: {res['pd_zone']}. Session: {res['session']} ({res['session_quality']}% quality).
            </p></div>""",
            unsafe_allow_html=True,
        )
        trend_class = "text-green" if res["trend_strong"] else "text-orange"
        st.markdown(
            f"""<div class="css-card"><small class="text-gold">📶 TREND STRENGTH</small><br/>
            <span class="{trend_class}" style="font-size:11px;">{'CONFIRMED' if res['trend_strong'] else 'NOT CONFIRMED'}</span></div>""",
            unsafe_allow_html=True,
        )
        integrity_rows = "".join(f"<div>{tf}: <b style='color:{'#00e676' if v=='LIVE' else '#ff5252'};'>{v}</b></div>" for tf, v in res["data_integrity"].items())
        st.markdown(f'<div class="css-card"><small class="text-gold">📡 DATA INTEGRITY</small><div style="font-size:10px; margin-top:6px;">{integrity_rows}</div></div>', unsafe_allow_html=True)

elif page == "Market Scanner":
    st.subheader("📊 Live Market Scanner")
    st.caption("Every row is a live call into generate_omega_signal() — the same function the Telegram worker uses.")
    rows = []
    progress = st.progress(0, text="Scanning...")
    for i, (label, ticker) in enumerate(ASSETS.items()):
        r = cached_signal(label, ticker, DEFAULT_MIN_TF_AGREEMENT, DEFAULT_MIN_SCORE, DEFAULT_MIN_RR)
        if r["ok"]:
            rows.append({"Asset": label, "Signal": r["bias"], "Score": r["score"], "Grade": grade(r["score"]),
                        "R:R": round(r["rr"], 2), "Session": r["session"], "Zone": r["pd_zone"],
                        "1D": r["tf_biases"]["1D"], "4H": r["tf_biases"]["4H"], "1H": r["tf_biases"]["1H"], "15M": r["tf_biases"]["15M"]})
        else:
            rows.append({"Asset": label, "Signal": "DATA DOWN", "Score": 0, "Grade": "-", "R:R": None,
                        "Session": "-", "Zone": "-", "1D": "-", "4H": "-", "1H": "-", "15M": "-"})
        progress.progress((i + 1) / len(ASSETS), text=f"Scanned {label}")
    progress.empty()
    table = pd.DataFrame(rows).sort_values("Score", ascending=False)
    st.dataframe(table, use_container_width=True, hide_index=True)

elif page == "Heatmap":
    st.subheader("🔥 Market Strength Heatmap")
    for label, ticker in ASSETS.items():
        r = cached_signal(label, ticker, DEFAULT_MIN_TF_AGREEMENT, DEFAULT_MIN_SCORE, DEFAULT_MIN_RR)
        if not r["ok"]:
            st.progress(0, text=f"{label} — DATA DOWN")
            continue
        direction = "Bullish" if r["bias"] == "BUY" else ("Bearish" if r["bias"] == "SELL" else "Neutral")
        st.progress(r["score"] / 100.0, text=f"{label} — {r['score']}/100 {direction} ({r['regime']['regime']})")

elif page == "AI Narrator":
    st.subheader("🤖 Katlego AI Narrator")
    asset_choice = st.selectbox("Asset", list(ASSETS.keys()), key="narrator_asset")
    r = cached_signal(asset_choice, ASSETS[asset_choice], DEFAULT_MIN_TF_AGREEMENT, DEFAULT_MIN_SCORE, DEFAULT_MIN_RR)
    if not r["ok"]:
        render_data_down(r)
    else:
        st.markdown(f"### {r['symbol']} — {r['bias']}")
        ob_state_label = "INVALIDATED" if r["ob_invalidated"] else ("MITIGATED" if r["ob_mitigated"] else "UNMITIGATED")
        narrative = (
            f"{r['symbol']} shows {r['structure']} on the 15M timeframe, in a {r['regime']['regime']} regime "
            f"(ADX {r['regime']['adx']}). {r['sweep_detail']}. Price sits in the {r['pd_zone']} zone relative to "
            f"the recent range equilibrium. The order block is {ob_state_label} "
            f"{r['ob_type']}. Trend strength is {'confirmed' if r['trend_strong'] else 'not confirmed'}. "
            f"Current session: {r['session']} ({r['session_quality']}% quality). "
            f"Composite score: {r['score']}/100 (Grade {grade(r['score'])})."
        )
        st.write(narrative)
        st.info("Generated directly from the computed values above — changes when the analysis changes, not a fixed template.")

elif page == "Multi-Timeframe":
    st.subheader("📈 Multi-Timeframe Alignment")
    asset_choice = st.selectbox("Asset", list(ASSETS.keys()), key="mtf_asset")
    r = cached_signal(asset_choice, ASSETS[asset_choice], DEFAULT_MIN_TF_AGREEMENT, DEFAULT_MIN_SCORE, DEFAULT_MIN_RR)
    if not r["ok"]:
        render_data_down(r)
    else:
        cols = st.columns(4)
        for col, tf in zip(cols, ["1D", "4H", "1H", "15M"]):
            with col:
                st.metric(tf, r["tf_biases"][tf])
                st.caption(r["tf_structures"][tf])

elif page == "Correlation Matrix":
    st.subheader("🔗 Live Rolling Correlation Matrix")
    matrix = compute_live_correlation_matrix()
    if matrix is None:
        st.warning("Correlation data unavailable.")
    else:
        st.dataframe(matrix.style.background_gradient(cmap="coolwarm", axis=None), use_container_width=True)

elif page == "Trade Journal":
    st.subheader("📒 Trade Journal")
    with st.form("journal_form", clear_on_submit=True):
        j_asset = st.selectbox("Asset", list(ASSETS.keys()))
        j_signal = st.selectbox("Signal Taken", ["BUY", "SELL"])
        j_entry = st.number_input("Entry Price", value=0.0, format="%.4f")
        j_stop = st.number_input("Stop Price", value=0.0, format="%.4f")
        j_tp1 = st.number_input("TP1 Price", value=0.0, format="%.4f")
        j_notes = st.text_area("Setup / execution notes")
        j_outcome = st.selectbox("Outcome", ["OPEN", "WIN", "LOSS", "BREAKEVEN"])
        j_submit = st.form_submit_button("Save Entry")
    if j_submit and j_notes:
        database.log_trade(j_asset, j_signal, j_entry, j_stop, j_tp1, j_outcome, j_notes)
        st.success("Saved.")
    trades = database.get_trades()
    if trades:
        st.dataframe(pd.DataFrame(trades), use_container_width=True, hide_index=True)
    else:
        st.info("No journal entries yet.")

elif page == "Performance":
    st.subheader("📉 Performance")
    perf = database.get_performance()
    if not perf["has_data"]:
        st.info("No resolved trades logged yet. Log outcomes in Trade Journal to see real stats here.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Trades Logged", perf["total_logged"])
        c2.metric("Resolved", perf["resolved"])
        c3.metric("Win Rate", f"{perf['win_rate']}%")

elif page == "Settings":
    st.subheader("⚙️ Engine Settings")
    st.write(f"Timeframes required to agree: **{DEFAULT_MIN_TF_AGREEMENT}/4**")
    st.write(f"Minimum score to fire a signal: **{DEFAULT_MIN_SCORE}/100**")
    st.write(f"Minimum R:R (to TP2): **{DEFAULT_MIN_RR}**")
    st.caption("These come from config.py — change them there (or via Railway env vars) to affect both the Dashboard and worker.py identically.")
    st.markdown("---")
    st.markdown("**Known limitations, stated plainly:**")
    st.markdown(
        "- Score is a rules-based heuristic — not backtested against logged outcomes yet.\n"
        "- No live economic news calendar is wired in.\n"
        "- This dashboard does not place trades — a real order button needs a broker execution bridge/EA."
    )
