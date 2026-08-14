"""
SEKWAILA OMEGA X — STREAMLIT LIVE ENGINE (stable minimal UI)

This is a cleaned, minimal but fully functional Streamlit UI that calls the
engine, displays the generated signal JSON, and exposes News + AI expanders.
It avoids complex layout that previously introduced placeholder syntax.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timezone

from config import (
    ASSETS, DEFAULT_MIN_TF_AGREEMENT, DEFAULT_MIN_SCORE, DEFAULT_MIN_RR,
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, WORKER_POLL_SECONDS,
)
# Import engine lazily with a safe fallback so a failing engine import doesn't
# prevent the whole Streamlit app from starting. This lets us show an
# informative message in the UI instead of crashing the process during import.
try:
    from signals.signal_engine import generate_omega_signal
except Exception as _engine_exc:
    generate_omega_signal = None
    _engine_exc = _engine_exc

import news
import ai_provider
from settings_store import load_settings

st.set_page_config(page_title="SEKWAILA OMEGA X", page_icon="👑", layout="wide")

st.markdown("""
<style>
.stApp{background:linear-gradient(135deg,#070b12,#0b111b 55%,#070a10);color:#f4f7fb}
[data-testid="stSidebar"]{background:#080d15}
</style>
""", unsafe_allow_html=True)

# Helper converters
def num(v, default=0.0):
    try:
        return float(v)
    except Exception:
        return default

# Sidebar
st.sidebar.title("SEKWAILA OMEGA X")
symbols = list(ASSETS.keys()) if ASSETS else []
if not symbols:
    st.sidebar.error("ASSETS is empty in config.py — add at least one symbol.")
    st.stop()

selected = st.sidebar.selectbox("Asset", symbols)
min_tf = st.sidebar.slider("Min TF agreement", 1, 4, int(DEFAULT_MIN_TF_AGREEMENT))
min_score = st.sidebar.slider("Min score", 0.0, 100.0, float(DEFAULT_MIN_SCORE))
min_rr = st.sidebar.number_input("Min R:R", 0.1, 10.0, float(DEFAULT_MIN_RR), 0.1)

st.sidebar.markdown("---")
st.sidebar.caption("Settings are persisted locally via settings_store")

# Main
st.title("👑 SEKWAILA OMEGA X — Live Engine")
st.caption(f"Selected: {selected} — ticker: {ASSETS.get(selected, 'N/A')}")

with st.spinner("Evaluating signal..."):
    try:
        if generate_omega_signal is None:
            # Lazy import failed earlier — show an informative result instead of crashing.
            raise ImportError(f"Engine import failed: {_engine_exc}")
        result = generate_omega_signal(selected, ASSETS.get(selected), min_tf=min_tf, min_score=min_score, min_rr=min_rr)
    except Exception as exc:
        result = {"ok": False, "symbol": selected, "ticker": ASSETS.get(selected), "reason": f"Engine unavailable: {exc}", "data_integrity": {}}

if not result.get("ok"):
    st.error(f"Engine could not evaluate {selected}: {result.get('reason','Unknown')}")
    if result.get("data_integrity"):
        st.subheader("Data Integrity")
        st.json(result.get("data_integrity"))
else:
    st.success(f"Signal: {result.get('bias','NEUTRAL')} — Score: {result.get('score')}")
    st.subheader("Signal JSON")
    st.json(result)

# News Intelligence
with st.expander("📰 News Intelligence"):
    st.markdown("Recent headlines (requires NEWSAPI_KEY env var)")
    headlines, articles = news.fetch_news_for_asset(selected)
    if not headlines:
        st.info("No headlines or NEWSAPI_KEY not configured.")
    else:
        for h in headlines[:12]:
            st.write("- ", h)
        settings = load_settings()
        ai_enabled = settings.get("ai", {}).get("enabled", False)
        if ai_enabled and headlines:
            if st.button("Summarise headlines (AI)"):
                with st.spinner("Summarising..."):
                    summary = news.summarise_headlines(headlines)
                    st.markdown("**AI Summary**")
                    st.write(summary)

# AI Narrator
with st.expander("🧠 AI Narrator"):
    st.markdown("Generate a short narrative for the current signal. AI must be enabled in Settings and OPENAI_API_KEY set.")
    settings = load_settings()
    ai_enabled = settings.get("ai", {}).get("enabled", False)
    if not ai_enabled:
        st.info("AI Narrator is disabled in settings.")
        try:
            st.code(ai_provider._local_summarize_signal(result))
        except Exception:
            st.write("(no local summary available)")
    else:
        if st.button("Generate AI Narrative"):
            with st.spinner("Calling AI provider..."):
                try:
                    summary = ai_provider.summarize_signal(result)
                    st.markdown("**AI Narrative**")
                    st.write(summary)
                except Exception as exc:
                    st.error(f"AI error: {exc}")

st.markdown("---")
st.caption(f"Auto-refresh every {WORKER_POLL_SECONDS}s when tab active — {datetime.now(timezone.utc).isoformat()}")
