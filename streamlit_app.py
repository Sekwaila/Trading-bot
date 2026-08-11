"""
SEKWAILA OMEGA X — STREAMLIT TRADING TERMINAL

Entry point for Streamlit Cloud. All signal computation happens in
signals/signal_engine.py — this file only renders it. The Telegram "Test"
button in Settings sends through telegram_bot.py using the same engine
result, so the dashboard and any Telegram alert always agree.
"""

import time
from datetime import datetime, timezone

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from config import ASSETS, TF_ORDER
from signals.signal_engine import (
    generate_omega_signal,
    calculate_position_size_for_symbol,
    fetch_usdzar_rate,
)
from classification import classify_signal, level_rank, glow_class
from settings_store import load_settings, save_settings
from telegram_bot import format_signal_message, send_telegram_message
from calibration import apply_offset
from live_price import get_live_price
import theme

st.set_page_config(page_title="SEKWAILA OMEGA X", page_icon="👑", layout="wide", initial_sidebar_state="collapsed")
theme.inject()

# ---------------------------------------------------------------------------
# Session state / routing
# ---------------------------------------------------------------------------
if "view" not in st.session_state: st.session_state.view = "home"
if "view_symbol" not in st.session_state: st.session_state.view_symbol = None
if "settings" not in st.session_state: st.session_state.settings = load_settings()

S = st.session_state.settings


def goto(view, symbol=None):
    st.session_state.view = view
    st.session_state.view_symbol = symbol


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def num(v, default=0.0):
    try:
        f = float(v)
        return f if pd.notna(f) else default
    except Exception:
        return default


def price(v, decimals=4):
    v = num(v)
    return "—" if v == 0 else f"{v:,.{decimals}f}"


def bias_css(v):
    v = str(v).upper()
    if v in ("BUY", "BULLISH"):
        return "buy"
    if v in ("SELL", "BEARISH"):
        return "sell"
    return "neutral"


@st.cache_data(ttl=None, show_spinner=False)
def _fetch_one(symbol, ticker, min_tf, min_score, min_rr, _bucket):
    """_bucket changes every refresh_seconds to bust the cache on a timer."""
    try:
        return generate_omega_signal(symbol, ticker, min_tf=min_tf, min_score=min_score, min_rr=min_rr)
    except Exception as exc:
        return {"ok": False, "symbol": symbol, "ticker": ticker, "reason": f"{type(exc).__name__}: {exc}"}


def fetch_all(selected_assets, min_tf, min_score, min_rr, refresh_seconds):
    bucket = int(time.time() // max(refresh_seconds, 5))
    out = {}
    for symbol in selected_assets:
        ticker = ASSETS.get(symbol)
        if not ticker:
            continue
        out[symbol] = _fetch_one(symbol, ticker, min_tf, min_score, min_rr, bucket)
    return out


# ---------------------------------------------------------------------------
# Top navigation (always visible)
# ---------------------------------------------------------------------------
nav_l, nav_m, nav_r = st.columns([1, 3, 1])
with nav_l:
    if st.session_state.view != "home":
        if st.button("← BACK", key="nav_back", width="stretch"):
            goto("home"); st.rerun()
    else:
        st.markdown("&nbsp;")
with nav_r:
    if st.button("⚙ SETTINGS", key="nav_settings", width="stretch"):
        goto("settings"); st.rerun()

refresh_seconds = int(S["general"]["refresh_seconds"])
if st.session_state.view == "home":
    st_autorefresh(interval=refresh_seconds * 1000, key="omega_refresh")

now_str = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
theme.header("ENGINE LIVE" if st.session_state.view != "settings" else "CONFIGURATION", now_str)

selected_assets = [a for a in S["data"]["selected_assets"] if a in ASSETS] or list(ASSETS.keys())
min_tf = int(S["signals"]["min_tf_agreement"])
min_score = float(S["signals"]["min_score"])
min_rr = float(S["signals"]["min_rr"])

# =============================================================================
# VIEW: SETTINGS
# =============================================================================
if st.session_state.view == "settings":
    st.markdown('<div class="nav-crumb">DASHBOARD / SETTINGS</div>', unsafe_allow_html=True)
    tabs = st.tabs(["GENERAL", "SIGNALS", "RISK", "AI", "TELEGRAM", "DATA", "DISPLAY"])

    with tabs[0]:
        st.subheader("General")
        S["general"]["refresh_seconds"] = st.selectbox(
            "Auto refresh interval (seconds)", [30, 60, 120, 300],
            index=[30, 60, 120, 300].index(S["general"]["refresh_seconds"]) if S["general"]["refresh_seconds"] in [30, 60, 120, 300] else 2,
        )
        S["general"]["account_currency"] = st.selectbox("Account currency", ["ZAR", "USD"], index=["ZAR", "USD"].index(S["general"]["account_currency"]))
        S["general"]["account_balance"] = st.number_input(f"Account balance ({S['general']['account_currency']})", min_value=0.0, value=float(S["general"]["account_balance"]), step=500.0)

    with tabs[1]:
        st.subheader("Signal engine thresholds")
        st.caption("These feed directly into generate_omega_signal() in signals/signal_engine.py.")
        S["signals"]["min_tf_agreement"] = st.slider("Minimum timeframe agreement", 1, len(TF_ORDER), int(S["signals"]["min_tf_agreement"]))
        S["signals"]["min_score"] = st.slider("Minimum score", 0.0, 100.0, float(S["signals"]["min_score"]))
        S["signals"]["min_rr"] = st.number_input("Minimum R:R", 0.1, 10.0, float(S["signals"]["min_rr"]), 0.1)
        st.caption("Classification tiers (EXTREME / STRONG / WEAK) are set in config.py — EXTREME_SCORE_MIN, STRONG_SCORE_MIN, WEAK_SCORE_MAX, EXTREME_MIN_TF_AGREEMENT.")

    with tabs[2]:
        st.subheader("Risk")
        S["risk"]["risk_pct"] = st.slider("Risk per trade (%)", 0.10, 5.00, float(S["risk"]["risk_pct"]), 0.10)

    with tabs[3]:
        st.subheader("AI")
        st.caption("The project does not currently call an AI provider. This section stores configuration for future integration only — it has no effect on signals yet.")
        S["ai"]["enabled"] = st.toggle("AI analysis enabled", value=bool(S["ai"]["enabled"]))
        S["ai"]["provider"] = st.selectbox("Provider", ["Anthropic", "OpenAI", "Other"], index=["Anthropic", "OpenAI", "Other"].index(S["ai"]["provider"]) if S["ai"]["provider"] in ["Anthropic", "OpenAI", "Other"] else 0)
        S["ai"]["api_key"] = st.text_input("API key", value=S["ai"]["api_key"], type="password")
        S["ai"]["model"] = st.text_input("Model", value=S["ai"]["model"], placeholder="e.g. claude-sonnet-4-6")
        S["ai"]["confidence_threshold"] = st.slider("Minimum AI confidence to surface", 0.0, 100.0, float(S["ai"]["confidence_threshold"]))
        S["ai"]["contributes_to_score"] = st.toggle("Let AI contribute to the score (not yet implemented)", value=bool(S["ai"]["contributes_to_score"]), disabled=True)

    with tabs[4]:
        st.subheader("Telegram")
        S["telegram"]["enabled"] = st.toggle("Telegram alerts enabled", value=bool(S["telegram"]["enabled"]))
        S["telegram"]["bot_token"] = st.text_input("Bot token", value=S["telegram"]["bot_token"], type="password", help="Never displayed in plain text after saving.")
        S["telegram"]["chat_id"] = st.text_input("Chat ID", value=S["telegram"]["chat_id"])
        S["telegram"]["min_signal_level"] = st.selectbox(
            "Minimum signal strength for alerts",
            ["WEAK BUY / WEAK SELL", "BUY / SELL", "STRONG BUY / STRONG SELL", "EXTREME BUY / EXTREME SELL"],
            index=["WEAK BUY", "BUY", "STRONG BUY", "EXTREME BUY"].index(S["telegram"]["min_signal_level"]) if S["telegram"]["min_signal_level"] in ["WEAK BUY", "BUY", "STRONG BUY", "EXTREME BUY"] else 2,
        ).split(" /")[0].strip()
        S["telegram"]["cooldown_minutes"] = st.number_input("Alert cooldown (minutes)", min_value=0, value=int(S["telegram"]["cooldown_minutes"]), step=5)
        st.caption("worker.py runs these same alerts automatically in the background — it reads signals/signal_engine.py directly, same as this dashboard, so they can never disagree.")
        if st.button("📨 Send test message"):
            ok, detail = send_telegram_message(S["telegram"]["bot_token"], S["telegram"]["chat_id"], "👑 SEKWAILA OMEGA X — test message. Telegram is wired up correctly.")
            (st.success if ok else st.error)(detail)

    with tabs[5]:
        st.subheader("Data")
        S["data"]["selected_assets"] = st.multiselect("Active pairs", list(ASSETS.keys()), default=S["data"]["selected_assets"])
        st.divider()
        st.subheader("Broker price calibration")
        st.caption(
            "Prices here come from Yahoo Finance, not your broker — they can differ from your "
            "MT5/terminal quote by a few points depending on feed and session. Enter the "
            "difference (your broker price minus this dashboard's price) for any pair below to "
            "shift entry/stop/TP1-3 so they line up with what your terminal shows. This does not "
            "change the engine's analysis — only the displayed price levels."
        )
        offsets = S["data"].get("price_offsets", {})
        for sym in S["data"]["selected_assets"]:
            offsets[sym] = st.number_input(f"{sym} offset", value=float(offsets.get(sym, 0.0)), step=0.10, format="%.4f", key=f"offset_{sym}")
        S["data"]["price_offsets"] = offsets

    with tabs[6]:
        st.subheader("Display")
        S["display"]["compact_mode"] = st.toggle("Compact card mode", value=bool(S["display"]["compact_mode"]))

    st.divider()
    c1, c2 = st.columns([1, 5])
    with c1:
        if st.button("💾 Save settings", type="primary"):
            save_settings(S)
            st.success("Settings saved.")

# =============================================================================
# VIEW: PAIR DETAIL
# =============================================================================
elif st.session_state.view == "pair":
    symbol = st.session_state.view_symbol
    st.markdown(f'<div class="nav-crumb">DASHBOARD / {symbol}</div>', unsafe_allow_html=True)

    results = fetch_all(selected_assets if symbol in selected_assets else selected_assets + [symbol], min_tf, min_score, min_rr, refresh_seconds)
    result = results.get(symbol)
    price_offset = float(S["data"].get("price_offsets", {}).get(symbol, 0.0))
    if result and result.get("ok") and price_offset:
        result = apply_offset(result, price_offset)

    if not result or not result.get("ok"):
        st.error(f"{symbol} — DATA UNAVAILABLE")
        st.caption(result.get("reason", "Unknown error") if result else "No result returned.")
        if result and result.get("data_integrity"):
            st.json(result["data_integrity"])
    else:
        level = classify_signal(result)
        css = glow_class(level)
        bull, bear = num(result.get("bull_score")), num(result.get("bear_score"))
        agreement = max(int(result.get("bull_tf_count", 0)), int(result.get("bear_tf_count", 0)))
        tf_count = len(result.get("tf_biases", {})) or len(TF_ORDER)

        st.markdown(
            f"""<div class="sig-card {css}">
                <div class="top-row">
                  <div><div class="sig-symbol">{symbol}</div><div class="sig-ticker">{result.get('ticker','')}</div></div>
                  {theme.badge_html(level, css)}
                </div>
                <div class="sig-meta">
                  <span>SCORE&nbsp; <b style="color:var(--text)">{result.get('score',0):.1f}/100</b></span>
                  <span>BIAS&nbsp; <b style="color:var(--text)">{result.get('bias','NEUTRAL')}</b></span>
                  <span>TF AGREEMENT&nbsp; <b style="color:var(--text)">{agreement}/{tf_count}</b></span>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )
        if result.get("bias") == "NEUTRAL" and result.get("reason"):
            st.caption(result["reason"])

        # ---- price levels ----
        theme.panel_open("Price &amp; Trade Levels")
        live = get_live_price(result.get("ticker", ""))
        if live and price_offset:
            live = live + price_offset
        if price_offset:
            st.caption(f"Calibrated {price_offset:+.4f} to match your broker. \"Entry\" is the last CLOSED candle (signal basis); \"Price\" is the live quote — a small gap between them is expected.")
        else:
            st.caption("\"Entry\" is the last CLOSED candle (signal basis); \"Price\" is the live quote. A small gap between them is expected — set a calibration offset in Settings > Data if you want them to match your broker exactly.")
        chips = "".join([
            theme.metric_chip("Price (live)", price(live) if live else "—"),
            theme.metric_chip("Entry", price(result.get("entry")), bias_css(result.get("bias"))),
            theme.metric_chip("Stop", price(result.get("stop")), "sell" if result.get("bias") != "NEUTRAL" else ""),
            theme.metric_chip("TP1", price(result.get("tp1")), "buy" if result.get("bias") != "NEUTRAL" else ""),
            theme.metric_chip("TP2", price(result.get("tp2")), "buy" if result.get("bias") != "NEUTRAL" else ""),
            theme.metric_chip("TP3", price(result.get("tp3")), "buy" if result.get("bias") != "NEUTRAL" else ""),
            theme.metric_chip("R:R", f"{num(result.get('rr')):.2f}" if result.get("rr") else "—"),
            theme.metric_chip("ATR", price(result.get("atr"))),
        ])
        st.markdown(f'<div class="chip-grid">{chips}</div>', unsafe_allow_html=True)
        theme.panel_close()

        # ---- position size ----
        if result.get("bias") in ("BUY", "SELL"):
            sizing_usd = S["general"]["account_balance"]
            zar_note = ""
            if S["general"]["account_currency"] == "ZAR":
                usd_zar = fetch_usdzar_rate()
                if usd_zar and usd_zar > 0:
                    sizing_usd = S["general"]["account_balance"] / usd_zar
                    zar_note = f"Live USD/ZAR: {usd_zar:.4f}"
                else:
                    sizing_usd = 0
            position = calculate_position_size_for_symbol(symbol, sizing_usd, S["risk"]["risk_pct"], result.get("entry", 0), result.get("stop", 0))
            theme.panel_open("Position Size" + (f" &middot; {zar_note}" if zar_note else ""))
            if position:
                chips = "".join([
                    theme.metric_chip("Risk amount", f"${position['risk_amount_usd']:,.2f}"),
                    theme.metric_chip("Stop distance", price(position["stop_distance"])),
                    theme.metric_chip("Lots", f"{position['lots']:.4f}"),
                    theme.metric_chip("Contract size", f"{position['contract_size']:g}"),
                ])
                st.markdown(f'<div class="chip-grid">{chips}</div>', unsafe_allow_html=True)
            else:
                st.info("Position size unavailable (check account balance / USD-ZAR rate).")
            theme.panel_close()

        # ---- timeframe agreement ----
        theme.panel_open("Multi-Timeframe Agreement")
        rows_html = ""
        for tf in TF_ORDER:
            if tf not in result.get("tf_biases", {}):
                continue
            b = result["tf_biases"][tf]
            s = result.get("tf_structures", {}).get(tf, "NONE")
            icon = "🟢" if b == "BUY" else "🔴" if b == "SELL" else "🟡"
            rows_html += f'<div class="tf-row"><span class="tf-label">{tf}</span><span style="flex:1;color:var(--dim)">{icon} {s}</span><span class="tf-pill {bias_css(b)}">{b}</span></div>'
        st.markdown(rows_html, unsafe_allow_html=True)
        st.caption(f"Bullish: {result.get('bull_tf_count',0)}/{tf_count} · Bearish: {result.get('bear_tf_count',0)}/{tf_count} · Required: {min_tf}/{tf_count}")
        theme.panel_close()

        # ---- indicators ----
        theme.panel_open("Indicator Panel")
        regime = result.get("regime", {})
        chips = "".join([
            theme.metric_chip("RSI (14)", f"{num(result.get('rsi')):.1f}"),
            theme.metric_chip("MACD trend", result.get("macd_trend", "NEUTRAL"), bias_css(result.get("macd_trend"))),
            theme.metric_chip("EMA cross", result.get("ema_cross", "NEUTRAL"), bias_css(result.get("ema_cross"))),
            theme.metric_chip("Price / VWAP", result.get("vwap_status", "UNKNOWN")),
            theme.metric_chip("ADX", f"{num(regime.get('adx')):.2f}"),
            theme.metric_chip("ATR (14)", price(result.get("atr"))),
            theme.metric_chip("Volatility", result.get("vol_status", "UNKNOWN")),
            theme.metric_chip("Trend strength", "STRONG" if result.get("trend_strong") else "WEAK", "buy" if result.get("trend_strong") else ""),
            theme.metric_chip("Market regime", regime.get("regime", "UNKNOWN")),
            theme.metric_chip("Vol ratio", f"{num(regime.get('vol_ratio'),1):.2f}"),
        ])
        st.markdown(f'<div class="chip-grid">{chips}</div>', unsafe_allow_html=True)
        st.caption(result.get("trend_detail", ""))
        theme.panel_close()

        # ---- smart money concepts ----
        pcol1, pcol2 = st.columns(2)
        with pcol1:
            theme.panel_open("Market Structure")
            zone = result.get("ob_zone")
            chips = "".join([
                theme.metric_chip("Structure", result.get("structure", "NONE")),
                theme.metric_chip("Order block", result.get("ob_type", "NONE")),
                theme.metric_chip("OB zone", f"{price(zone[0])} — {price(zone[1])}" if zone else "—"),
                theme.metric_chip("OB mitigated", "YES" if result.get("ob_mitigated") else "NO"),
                theme.metric_chip("OB invalidated", "YES" if result.get("ob_invalidated") else "NO", "sell" if result.get("ob_invalidated") else ""),
            ])
            st.markdown(f'<div class="chip-grid">{chips}</div>', unsafe_allow_html=True)
            theme.panel_close()

            theme.panel_open("Premium / Discount")
            pd_info = result.get("pd_info", {})
            chips = "".join([
                theme.metric_chip("Zone", result.get("pd_zone", "UNKNOWN")),
                theme.metric_chip("Equilibrium", price(pd_info.get("equilibrium"))),
                theme.metric_chip("Swing high", price(pd_info.get("swing_high"))),
                theme.metric_chip("Swing low", price(pd_info.get("swing_low"))),
            ])
            st.markdown(f'<div class="chip-grid">{chips}</div>', unsafe_allow_html=True)
            theme.panel_close()

        with pcol2:
            theme.panel_open("Liquidity &amp; Fair Value Gaps")
            fvg = result.get("fvg")
            fvg_zone = fvg.get("zone") if fvg else None
            chips = "".join([
                theme.metric_chip("Liquidity sweep", "YES" if result.get("sweep") else "NO", "buy" if result.get("sweep") else ""),
                theme.metric_chip("FVG type", fvg.get("type") if fvg else "NONE"),
                theme.metric_chip("FVG zone", f"{price(fvg_zone[0])} — {price(fvg_zone[1])}" if fvg_zone else "—"),
                theme.metric_chip("FVG filled", ("YES" if fvg.get("filled") else "NO") if fvg else "—"),
            ])
            st.markdown(f'<div class="chip-grid">{chips}</div>', unsafe_allow_html=True)
            st.caption(result.get("sweep_detail", "NO_SWEEP"))
            theme.panel_close()

            theme.panel_open("Equal Highs / Lows")
            eqh, eql = result.get("eq_highs", []), result.get("eq_lows", [])
            chips = "".join([
                theme.metric_chip("Equal highs", ", ".join(f"{v:.2f}" for v in eqh[-3:]) if eqh else "NONE"),
                theme.metric_chip("Equal lows", ", ".join(f"{v:.2f}" for v in eql[-3:]) if eql else "NONE"),
                theme.metric_chip("Session", result.get("session", "UNKNOWN")),
                theme.metric_chip("Session quality", f"{num(result.get('session_quality'),50):.0f}%"),
            ])
            st.markdown(f'<div class="chip-grid">{chips}</div>', unsafe_allow_html=True)
            theme.panel_close()

        # ---- chart ----
        theme.panel_open("Chart")
        available_tfs = [tf for tf in TF_ORDER if result.get("data", {}).get(tf) is not None]
        if available_tfs:
            chosen_tf = st.radio("Timeframe", available_tfs, index=len(available_tfs) - 1, horizontal=True, key=f"tf_{symbol}")
            df = result["data"][chosen_tf].tail(180)
            fig = go.Figure(go.Candlestick(x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"], name=chosen_tf,
                                            increasing_line_color="#22e6a3", decreasing_line_color="#ff4d6a"))
            if result.get("bias") in ("BUY", "SELL"):
                for name, val, color in [("Entry", result.get("entry"), "#8592a8"), ("Stop", result.get("stop"), "#ff4d6a"),
                                          ("TP1", result.get("tp1"), "#22e6a3"), ("TP2", result.get("tp2"), "#22e6a3"), ("TP3", result.get("tp3"), "#22e6a3")]:
                    v = num(val)
                    if v > 0:
                        fig.add_hline(y=v, line_dash="dash", line_color=color, annotation_text=f"{name} {price(v)}", annotation_font_color=color)
            vwap = num(result.get("vwap_val"))
            if vwap > 0:
                fig.add_hline(y=vwap, line_dash="dot", line_color="#ffb238", annotation_text=f"VWAP {price(vwap)}")
            fig.update_layout(template="plotly_dark", height=520, margin=dict(l=10, r=10, t=20, b=10),
                               xaxis_rangeslider_visible=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, width="stretch", config={"displaylogo": False, "responsive": True})
        else:
            st.info("No chart data available for this pair.")
        theme.panel_close()

        with st.expander("🛡️ Data integrity"):
            integrity = result.get("data_integrity", {})
            if integrity:
                st.dataframe(pd.DataFrame([{"Timeframe": tf, "Status": s} for tf, s in integrity.items()]), width="stretch", hide_index=True)
            st.caption("The engine removes the currently forming candle before indicator and structure calculations.")

# =============================================================================
# VIEW: HOME
# =============================================================================
else:
    st.markdown('<div class="nav-crumb">LIVE SIGNALS</div>', unsafe_allow_html=True)
    st.warning("⚠️ Informational only. Not financial advice. Score is a rules-based heuristic — not a guarantee.")

    if not selected_assets:
        st.info("No pairs selected. Choose active pairs in Settings → Data.")
    else:
        with st.spinner("Evaluating pairs..."):
            results = fetch_all(selected_assets, min_tf, min_score, min_rr, refresh_seconds)

        ranked = []
        for symbol, result in results.items():
            offset = float(S["data"].get("price_offsets", {}).get(symbol, 0.0))
            if result and result.get("ok") and offset:
                result = apply_offset(result, offset)
                results[symbol] = result
            level = classify_signal(result)
            ranked.append((level_rank(level), symbol, result, level))
        ranked.sort(key=lambda r: (r[0], -(num(r[2].get("score")) if r[2] else -1)))

        cols = st.columns(2)
        for i, (_, symbol, result, level) in enumerate(ranked):
            css = glow_class(level)
            with cols[i % 2]:
                if not result or not result.get("ok"):
                    st.markdown(
                        f"""<div class="sig-card {css}">
                            <div class="top-row"><div class="sig-symbol">{symbol}</div>{theme.badge_html(level, css)}</div>
                            <div class="sig-meta"><span>{(result or {}).get('reason','No data returned.')[:70]}</span></div>
                        </div>""",
                        unsafe_allow_html=True,
                    )
                else:
                    agreement = max(int(result.get("bull_tf_count", 0)), int(result.get("bear_tf_count", 0)))
                    tf_count = len(result.get("tf_biases", {})) or len(TF_ORDER)
                    card_offset = float(S["data"].get("price_offsets", {}).get(symbol, 0.0))
                    card_live = get_live_price(result.get("ticker", ""))
                    if card_live and card_offset:
                        card_live = card_live + card_offset
                    card_price = price(card_live) if card_live else price(result.get("entry"))
                    st.markdown(
                        f"""<div class="sig-card {css}">
                            <div class="top-row">
                              <div><div class="sig-symbol">{symbol}</div><div class="sig-ticker">{result.get('ticker','')}</div></div>
                              {theme.badge_html(level, css)}
                            </div>
                            <div class="sig-meta">
                              <span>SCORE&nbsp;<b style="color:var(--text)">{result.get('score',0):.1f}</b></span>
                              <span>PRICE&nbsp;<b style="color:var(--text)">{card_price}</b></span>
                              <span>TF&nbsp;<b style="color:var(--text)">{agreement}/{tf_count}</b></span>
                            </div>
                        </div>""",
                        unsafe_allow_html=True,
                    )
                if st.button(f"Open {symbol} →", key=f"open_{symbol}", width="stretch"):
                    goto("pair", symbol); st.rerun()

st.markdown("---")
st.caption(f"SEKWAILA OMEGA X · signals/signal_engine.py is the single source of truth for dashboard and Telegram · {now_str}")
