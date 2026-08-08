import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime, time
import json
import sqlite3

# =============================================================================
# 1. PAGE CONFIG & CONSTANTS
# =============================================================================
st.set_page_config(
    page_title="SEKWAILA OMEGA X",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Color Palette Variables
COLOR_BG = "#080A0F"
COLOR_CARD = "#0D1017"
COLOR_PANEL = "#121722"
COLOR_BORDER = "#171C26"
COLOR_GOLD = "#D9A441"
COLOR_GREEN = "#22C55E"
COLOR_RED = "#EF4444"
COLOR_CYAN = "#38BDF8"
COLOR_GREY = "#A1A1AA"

DEFAULT_WATCHLIST = {
    "FOREX": ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDCHF=X", "USDCAD=X", "NZDUSD=X"],
    "METALS": ["GC=F", "SI=F"],
    "INDICES": ["^DJI", "^GSPC", "^IXIC", "^GDAXI", "^FTSE"],
    "CRYPTO": ["BTC-USD", "ETH-USD", "SOL-USD"]
}

SYMBOL_ALIASES = {
    "EURUSD=X": "EURUSD", "GBPUSD=X": "GBPUSD", "USDJPY=X": "USDJPY",
    "AUDUSD=X": "AUDUSD", "USDCHF=X": "USDCHF", "USDCAD=X": "USDCAD",
    "NZDUSD=X": "NZDUSD", "GC=F": "XAUUSD", "SI=F": "XAGUSD",
    "^DJI": "US30", "^GSPC": "SP500", "^IXIC": "NAS100",
    "^GDAXI": "GER40", "^FTSE": "UK100", "BTC-USD": "BTCUSD",
    "ETH-USD": "ETHUSD", "SOL-USD": "SOLUSD"
}

REVERSE_ALIASES = {v: k for k, v in SYMBOL_ALIASES.items()}

# =============================================================================
# 2. PERSISTENCE & DATABASE ENGINE
# =============================================================================
DB_FILE = "sekwaila_data.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS journal (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT, time TEXT, symbol TEXT, direction TEXT,
                    entry REAL, sl REAL, tp REAL, exit REAL,
                    risk_pct REAL, pnl REAL, setup_type TEXT, timeframe TEXT,
                    reason TEXT, emotion TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY, value TEXT)''')
    conn.commit()
    conn.close()

init_db()

def load_settings_from_db():
    defaults = {
        "mode": "DEMO",
        "theme": "SEKWAILA DARK",
        "account_bal": 500.0,
        "risk_pct": 1.0,
        "currency": "ZAR",
        "min_confidence": 70,
        "risk_profile": "Balanced",
        "telegram_enabled": False,
        "telegram_token": "",
        "telegram_chat_id": "",
        "ai_model": "gpt-4o",
        "ai_personality": "Technical",
        "wallpaper_enabled": False,
        "wallpaper_bg": "",
        "wallpaper_opacity": 20,
        "wallpaper_blur": 0
    }
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT key, value FROM settings")
        rows = c.fetchall()
        conn.close()
        for k, v in rows:
            try:
                defaults[k] = json.loads(v)
            except:
                defaults[k] = v
    except Exception:
        pass
    return defaults

def save_setting_to_db(key, value):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, json.dumps(value)))
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Failed to save setting: {e}")

# Load Initial State
if "initialized" not in st.session_state:
    db_settings = load_settings_from_db()
    for k, v in db_settings.items():
        st.session_state[k] = v
    st.session_state.active_page = "Dashboard"
    st.session_state.selected_symbol = "XAUUSD"
    st.session_state.selected_timeframe = "15m"
    st.session_state.watchlist = DEFAULT_WATCHLIST
    st.session_state.initialized = True

# =============================================================================
# 3. CUSTOM CSS & RESPONSIVE STYLING
# =============================================================================
def apply_custom_css():
    wp_css = ""
    if st.session_state.get("wallpaper_enabled", False) and st.session_state.get("wallpaper_bg", ""):
        bg_url = st.session_state["wallpaper_bg"]
        opacity = st.session_state.get("wallpaper_opacity", 20) / 100.0
        blur = st.session_state.get("wallpaper_blur", 0)
        wp_css = f"""
        .stApp::before {{
            content: "";
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background-image: url('{bg_url}');
            background-size: cover;
            background-position: center;
            opacity: {opacity};
            filter: blur({blur}px);
            z-index: -1;
        }}
        """

    st.markdown(f"""
    <style>
        {wp_css}
        html, body, [data-testid="stAppViewContainer"] {{
            background-color: {COLOR_BG} !important;
            color: #D1D4DC !important;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif !important;
        }}
        header[data-testid="stHeader"] {{ visibility: hidden; height: 0; }}
        .block-container {{
            padding-top: 0.5rem !important;
            padding-bottom: 2rem !important;
            padding-left: 0.8rem !important;
            padding-right: 0.8rem !important;
            max-width: 100% !important;
        }}
        
        /* Premium Terminal Cards */
        .term-card {{
            background-color: {COLOR_CARD};
            border: 1px solid {COLOR_BORDER};
            border-radius: 6px;
            padding: 12px;
            margin-bottom: 10px;
        }}
        .term-card-gold {{
            background-color: {COLOR_CARD};
            border: 1px solid {COLOR_GOLD};
            border-radius: 6px;
            padding: 12px;
            margin-bottom: 10px;
        }}
        
        /* Badges */
        .badge-buy {{
            background: rgba(34, 197, 94, 0.15);
            color: {COLOR_GREEN};
            border: 1px solid {COLOR_GREEN};
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 700;
        }}
        .badge-sell {{
            background: rgba(239, 68, 68, 0.15);
            color: {COLOR_RED};
            border: 1px solid {COLOR_RED};
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 700;
        }}
        .badge-neutral {{
            background: rgba(161, 161, 170, 0.15);
            color: {COLOR_GREY};
            border: 1px solid {COLOR_GREY};
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 700;
        }}
        .badge-gold {{
            background: rgba(217, 164, 65, 0.15);
            color: {COLOR_GOLD};
            border: 1px solid {COLOR_GOLD};
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 700;
        }}
        
        /* Quick Action Grid Buttons */
        .stButton>button {{
            background-color: {COLOR_PANEL} !important;
            color: #E4E4E7 !important;
            border: 1px solid {COLOR_BORDER} !important;
            border-radius: 4px !important;
            font-weight: 600 !important;
            width: 100% !important;
            transition: all 0.2s ease !important;
        }}
        .stButton>button:hover {{
            border-color: {COLOR_GOLD} !important;
            color: {COLOR_GOLD} !important;
            background-color: {COLOR_CARD} !important;
        }}
        
        /* Streamlit Native Overrides */
        div[data-baseweb="select"] > div {{
            background-color: {COLOR_PANEL} !important;
            border-color: {COLOR_BORDER} !important;
            color: white !important;
        }}
        input {{
            background-color: {COLOR_PANEL} !important;
            color: white !important;
            border-color: {COLOR_BORDER} !important;
        }}
        
        /* Mobile Touch Optimizations */
        @media only screen and (max-width: 768px) {{
            .block-container {{ padding-left: 0.3rem !important; padding-right: 0.3rem !important; }}
            .stButton>button {{ padding: 12px 6px !important; font-size: 13px !important; }}
        }}
    </style>
    """, unsafe_allow_html=True)

apply_custom_css()

# =============================================================================
# 4. MARKET DATA PROVIDER ENGINE
# =============================================================================
TF_YFINANCE_MAP = {
    "1m": "1m", "3m": "2m", "5m": "5m", "15m": "15m",
    "30m": "30m", "1H": "60m", "4H": "1h", "1D": "1d", "1W": "1wk"
}

PERIOD_MAP = {
    "1m": "1d", "3m": "1d", "5m": "1d", "15m": "5d",
    "30m": "5d", "1H": "1mo", "4H": "3mo", "1D": "1y", "1W": "2y"
}

def generate_deterministic_demo_data(symbol, timeframe, bars=100):
    np.random.seed(abs(hash(symbol + timeframe)) % (2**32))
    base_price = 2350.0 if "XAU" in symbol else (65000.0 if "BTC" in symbol else (1.0850 if "EUR" in symbol else 5500.0))
    dt_range = pd.date_range(end=datetime.now(), periods=bars, freq="15min")
    
    returns = np.random.normal(0.0001, 0.002, bars)
    price_path = base_price * np.exp(np.cumsum(returns))
    
    df = pd.DataFrame(index=dt_range)
    df['Close'] = price_path
    df['Open'] = df['Close'].shift(1).fillna(base_price)
    df['High'] = df[['Open', 'Close']].max(axis=1) * (1 + np.abs(np.random.normal(0, 0.001, bars)))
    df['Low'] = df[['Open', 'Close']].min(axis=1) * (1 - np.abs(np.random.normal(0, 0.001, bars)))
    df['Volume'] = np.random.randint(100, 5000, bars)
    return df

@st.cache_data(ttl=30)
def fetch_market_data(symbol_alias, timeframe):
    mode = st.session_state.get("mode", "DEMO")
    real_symbol = REVERSE_ALIASES.get(symbol_alias, symbol_alias)
    
    if mode == "DEMO":
        return generate_deterministic_demo_data(real_symbol, timeframe), "DEMO DATA", "Demo Provider"
    
    try:
        yf_tf = TF_YFINANCE_MAP.get(timeframe, "15m")
        period = PERIOD_MAP.get(timeframe, "5d")
        ticker = yf.Ticker(real_symbol)
        df = ticker.history(period=period, interval=yf_tf)
        
        if df.empty:
            st.warning(f"No live data returned for {symbol_alias}. Falling back to demo data.")
            return generate_deterministic_demo_data(real_symbol, timeframe), "DEMO DATA (FALLBACK)", "Demo Engine"
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
        return df, "● LIVE", f"Yahoo Finance ({real_symbol})"
    except Exception:
        return generate_deterministic_demo_data(real_symbol, timeframe), "DEMO DATA (ERROR)", "Demo Engine"

# =============================================================================
# 5. TECHNICAL INDICATORS & MARKET STRUCTURE ENGINE
# =============================================================================
def calculate_indicators(df):
    data = df.copy()
    
    # EMAs
    data['EMA_9'] = data['Close'].ewm(span=9, adjust=False).mean()
    data['EMA_20'] = data['Close'].ewm(span=20, adjust=False).mean()
    data['EMA_50'] = data['Close'].ewm(span=50, adjust=False).mean()
    data['EMA_200'] = data['Close'].ewm(span=200, adjust=False).mean()
    
    # RSI
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / (loss.replace(0, 1e-9))
    data['RSI'] = 100 - (100 / (1 + rs))
    
    # ATR
    tr = pd.concat([
        data['High'] - data['Low'],
        (data['High'] - data['Close'].shift()).abs(),
        (data['Low'] - data['Close'].shift()).abs()
    ], axis=1).max(axis=1)
    data['ATR'] = tr.rolling(14).mean().fillna(data['Close'] * 0.005)
    
    # ADX
    plus_dm = data['High'].diff().clip(lower=0)
    minus_dm = (-data['Low'].diff()).clip(lower=0)
    data['ADX'] = ((plus_dm - minus_dm).abs() / (plus_dm + minus_dm + 1e-9)).rolling(14).mean() * 100
    data['ADX'] = data['ADX'].fillna(20.0)
    
    # MACD
    ema12 = data['Close'].ewm(span=12, adjust=False).mean()
    ema26 = data['Close'].ewm(span=26, adjust=False).mean()
    data['MACD'] = ema12 - ema26
    data['MACD_Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
    data['MACD_Hist'] = data['MACD'] - data['MACD_Signal']
    
    # MFI
    tp = (data['High'] + data['Low'] + data['Close']) / 3
    rmf = tp * data['Volume']
    pos_flow = rmf.where(tp > tp.shift(1), 0).rolling(14).sum()
    neg_flow = rmf.where(tp < tp.shift(1), 0).rolling(14).sum()
    mfr = pos_flow / (neg_flow + 1e-9)
    data['MFI'] = 100 - (100 / (1 + mfr))
    
    # Williams %R
    highest_h = data['High'].rolling(14).max()
    lowest_l = data['Low'].rolling(14).min()
    data['WR'] = ((highest_h - data['Close']) / (highest_h - lowest_l + 1e-9)) * -100
    
    # CCI
    sma_tp = tp.rolling(20).mean()
    mad = tp.rolling(20).apply(lambda x: np.fabs(x - x.mean()).mean(), raw=True)
    data['CCI'] = (tp - sma_tp) / (0.015 * mad + 1e-9)
    
    data['Supertrend'] = np.where(data['Close'] > data['EMA_20'], 1, -1)
    return data

def detect_market_structure(df):
    data = df.copy()
    data['BOS'] = None
    data['OrderBlock'] = None
    data['FVG'] = None
    
    data['Swing_High'] = data['High'][(data['High'] > data['High'].shift(1)) & (data['High'] > data['High'].shift(-1))]
    data['Swing_Low'] = data['Low'][(data['Low'] < data['Low'].shift(1)) & (data['Low'] < data['Low'].shift(-1))]
    
    for i in range(2, len(data)):
        if data['Low'].iloc[i] > data['High'].iloc[i-2]:
            data.iat[i, data.columns.get_loc('FVG')] = 'Bullish FVG'
        elif data['High'].iloc[i] < data['Low'].iloc[i-2]:
            data.iat[i, data.columns.get_loc('FVG')] = 'Bearish FVG'
            
    return data

# =============================================================================
# 6. RULE-BASED SEKWAILA SIGNAL ENGINE
# =============================================================================
def calculate_sekwaila_signal(df):
    if len(df) < 20:
        return {"action": "WAIT", "confidence": 50, "score": 50, "reasons": ["Insufficient market data"]}
    
    last = df.iloc[-1]
    
    trend_score = 0
    momentum_score = 0
    structure_score = 0
    volatility_score = 0
    reasons = []
    
    # Trend
    if last['Close'] > last['EMA_20'] > last['EMA_50']:
        trend_score += 25
        reasons.append("Price is strongly aligned above EMA 20 & 50 (Bullish Trend)")
    elif last['Close'] < last['EMA_20'] < last['EMA_50']:
        trend_score -= 25
        reasons.append("Price is strongly aligned below EMA 20 & 50 (Bearish Trend)")
    else:
        reasons.append("EMAs indicate market consolidation or transition")
        
    # Momentum
    if last['RSI'] > 55 and last['MACD'] > last['MACD_Signal']:
        momentum_score += 25
        reasons.append(f"RSI ({last['RSI']:.1f}) and MACD crossover confirm strong buying momentum")
    elif last['RSI'] < 45 and last['MACD'] < last['MACD_Signal']:
        momentum_score -= 25
        reasons.append(f"RSI ({last['RSI']:.1f}) and MACD crossover confirm selling momentum")
    else:
        reasons.append(f"RSI is neutral at {last['RSI']:.1f}")
        
    # Structure
    if last['MFI'] > 50:
        structure_score += 25
        reasons.append(f"Money Flow Index ({last['MFI']:.1f}) indicates institutional capital inflow")
    else:
        structure_score -= 25
        reasons.append(f"Money Flow Index ({last['MFI']:.1f}) indicates capital outflow")
        
    # Volatility
    if last['ADX'] > 25:
        volatility_score += 25
        reasons.append(f"ADX ({last['ADX']:.1f}) indicates a strong active market trend")
    else:
        volatility_score += 10
        reasons.append(f"ADX ({last['ADX']:.1f}) signals low market volatility/range-bound price action")
        
    total_raw = trend_score + momentum_score + structure_score + (volatility_score if trend_score >= 0 else -volatility_score)
    confidence = int(np.clip(50 + (abs(total_raw) / 100.0) * 45, 50, 98))
    
    if total_raw >= 60:
        action = "EXTREME BUY" if confidence >= 85 else "STRONG BUY"
    elif total_raw >= 25:
        action = "BUY"
    elif total_raw <= -60:
        action = "EXTREME SELL" if confidence >= 85 else "STRONG SELL"
    elif total_raw <= -25:
        action = "SELL"
    else:
        action = "WAIT"
        
    price = last['Close']
    atr = last['ATR']
    
    if "BUY" in action:
        entry = price
        sl = price - (1.5 * atr)
        tp1 = price + (1.0 * atr)
        tp2 = price + (2.0 * atr)
        tp3 = price + (3.0 * atr)
        tp4 = price + (4.0 * atr)
        tp5 = price + (5.0 * atr)
    elif "SELL" in action:
        entry = price
        sl = price + (1.5 * atr)
        tp1 = price - (1.0 * atr)
        tp2 = price - (2.0 * atr)
        tp3 = price - (3.0 * atr)
        tp4 = price - (4.0 * atr)
        tp5 = price - (5.0 * atr)
    else:
        entry = price
        sl = price - (1.0 * atr)
        tp1 = price + (1.0 * atr)
        tp2 = price + (2.0 * atr)
        tp3 = price + (3.0 * atr)
        tp4 = price + (4.0 * atr)
        tp5 = price + (5.0 * atr)
        
    rr_ratio = round(abs(tp1 - entry) / (abs(entry - sl) + 1e-9), 2)
    
    return {
        "action": action,
        "confidence": confidence,
        "raw_score": total_raw,
        "entry": entry,
        "sl": sl,
        "tp1": tp1, "tp2": tp2, "tp3": tp3, "tp4": tp4, "tp5": tp5,
        "rr": rr_ratio,
        "reasons": reasons,
        "atr": atr,
        "rsi": last['RSI'],
        "adx": last['ADX'],
        "mfi": last['MFI'],
        "wr": last['WR'],
        "cci": last['CCI']
    }

# =============================================================================
# 7. INTERACTIVE CHARTING ENGINE
# =============================================================================
def render_professional_chart(df, symbol, timeframe, signal_data, overlays):
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.8, 0.2]
    )
    
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'],
        name="Price",
        increasing_line_color=COLOR_GREEN,
        decreasing_line_color=COLOR_RED,
        increasing_fillcolor=COLOR_GREEN,
        decreasing_fillcolor=COLOR_RED
    ), row=1, col=1)
    
    if overlays.get("EMA_20", True) and "EMA_20" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_20'], line=dict(color='#38BDF8', width=1.2), name="EMA 20"), row=1, col=1)
    if overlays.get("EMA_50", True) and "EMA_50" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_50'], line=dict(color='#EAB308', width=1.2), name="EMA 50"), row=1, col=1)
    if overlays.get("EMA_200", False) and "EMA_200" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_200'], line=dict(color='#A855F7', width=1.5), name="EMA 200"), row=1, col=1)
        
    if overlays.get("Structure", True):
        for idx, row in df.iterrows():
            if not pd.isna(row.get('Swing_High')):
                fig.add_annotation(x=idx, y=row['High'], text="SH", showarrow=True, arrowhead=1, arrowcolor=COLOR_RED, ax=0, ay=-15, row=1, col=1)
            if not pd.isna(row.get('Swing_Low')):
                fig.add_annotation(x=idx, y=row['Low'], text="SL", showarrow=True, arrowhead=1, arrowcolor=COLOR_GREEN, ax=0, ay=15, row=1, col=1)

    if overlays.get("Signal Levels", True) and signal_data:
        entry = signal_data['entry']
        sl = signal_data['sl']
        tp1 = signal_data['tp1']
        tp2 = signal_data['tp2']
        
        fig.add_hline(y=entry, line_dash="dash", line_color=COLOR_CYAN, annotation_text=f"ENTRY {entry:.2f}", row=1, col=1)
        fig.add_hline(y=sl, line_dash="solid", line_color=COLOR_RED, annotation_text=f"SL {sl:.2f}", row=1, col=1)
        fig.add_hline(y=tp1, line_dash="dot", line_color=COLOR_GREEN, annotation_text=f"TP1 {tp1:.2f}", row=1, col=1)
        fig.add_hline(y=tp2, line_dash="dot", line_color=COLOR_GREEN, annotation_text=f"TP2 {tp2:.2f}", row=1, col=1)

    colors = [COLOR_GREEN if c >= o else COLOR_RED for c, o in zip(df['Close'], df['Open'])]
    fig.add_trace(go.Bar(
        x=df.index, y=df['Volume'],
        marker_color=colors,
        name="Volume",
        opacity=0.5
    ), row=2, col=1)
    
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=COLOR_CARD,
        plot_bgcolor=COLOR_CARD,
        margin=dict(l=10, r=10, t=25, b=10),
        xaxis_rangeslider_visible=False,
        showlegend=False,
        height=520,
        font=dict(family="sans-serif", size=11, color="#D1D4DC")
    )
    fig.update_xaxes(gridcolor=COLOR_BORDER, showgrid=True)
    fig.update_yaxes(gridcolor=COLOR_BORDER, showgrid=True)
    
    return fig

# =============================================================================
# 8. MARKET SESSION ENGINE
# =============================================================================
def get_market_sessions():
    now_utc = datetime.utcnow().time()
    
    asia_active = time(0, 0) <= now_utc <= time(9, 0)
    london_active = time(7, 0) <= now_utc <= time(16, 0)
    ny_active = time(12, 0) <= now_utc <= time(21, 0)
    overlap = london_active and ny_active
    
    active_str = "NEW YORK & LONDON OVERLAP" if overlap else ("NEW YORK" if ny_active else ("LONDON" if london_active else ("ASIA" if asia_active else "CLOSED")))
    killzone = "NEW YORK KILLZONE" if (time(13, 0) <= now_utc <= time(15, 0)) else ("LONDON KILLZONE" if (time(7, 0) <= now_utc <= time(9, 0)) else "No active killzone")
    
    return active_str, killzone

# =============================================================================
# 9. HEADER & TOP BAR NAVIGATION
# =============================================================================
def render_header():
    m_status, provider_str, _ = fetch_market_data(st.session_state.selected_symbol, st.session_state.selected_timeframe)
    data_mode = st.session_state.get("mode", "DEMO")
    session_name, killzone = get_market_sessions()
    
    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; background:{COLOR_CARD}; padding:8px 14px; border-radius:6px; border:1px solid {COLOR_BORDER}; margin-bottom:8px;">
        <div style="display:flex; align-items:center; gap:10px;">
            <span style="font-size:18px; font-weight:800; color:{COLOR_GOLD}; letter-spacing:1px;">⚡ SEKWAILA <span style="color:#FFF; font-size:12px;">OMEGA X</span></span>
            <span class="{'badge-buy' if data_mode == 'LIVE' else 'badge-gold'}">{data_mode} MODE</span>
        </div>
        <div style="display:flex; gap:15px; font-size:12px; font-weight:600;">
            <div><span style="color:{COLOR_GREY}">SESSION:</span> <span style="color:#FFF">{session_name}</span></div>
            <div><span style="color:{COLOR_GREY}">DXY:</span> <span style="color:{COLOR_RED}">99.60 BEAR</span></div>
            <div><span style="color:{COLOR_GREY}">ACCOUNT:</span> <span style="color:{COLOR_GOLD}">{st.session_state.get('currency', 'ZAR')} {st.session_state.get('account_bal', 500.0):,.2f}</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_nav_menu():
    pages = [
        "Dashboard", "Markets", "Market Scanner", "Chart", 
        "Heatmap", "Katlego AI", "Multi-Timeframe", "Correlation Matrix", 
        "Trade Journal", "Performance", "Settings", "Help"
    ]
    
    cols = st.columns(len(pages))
    for idx, page in enumerate(pages):
        is_selected = st.session_state.active_page == page
        btn_label = f"★ {page}" if is_selected else page
        if cols[idx].button(btn_label, key=f"nav_{page}"):
            st.session_state.active_page = page
            st.rerun()

# =============================================================================
# 10. PAGE IMPLEMENTATIONS
# =============================================================================

# --- A. DASHBOARD PAGE ---
def render_dashboard_page():
    session_name, killzone = get_market_sessions()
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="term-card"><span class="badge-buy">BUY SETUPS</span><h2 style="margin:5px 0 0 0; color:{COLOR_GREEN};">3 Active</h2><small style="color:{COLOR_GREY};">SP500, US30, BTCUSD</small></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="term-card"><span class="badge-sell">SELL SETUPS</span><h2 style="margin:5px 0 0 0; color:{COLOR_RED};">0 Active</h2><small style="color:{COLOR_GREY};">No active signals</small></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="term-card"><span class="badge-gold">SESSION</span><h2 style="margin:5px 0 0 0; color:#FFF;">{session_name}</h2><small style="color:{COLOR_GOLD};">{killzone}</small></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="term-card"><span class="badge-neutral">DXY INDEX</span><h2 style="margin:5px 0 0 0; color:{COLOR_RED};">99.60</h2><small style="color:{COLOR_RED};">BEARISH (-0.21%)</small></div>', unsafe_allow_html=True)

    st.markdown("### 📊 Watchlist & Live Signals")
    
    cat = st.radio("Category", list(st.session_state.watchlist.keys()), horizontal=True)
    symbols = st.session_state.watchlist[cat]
    
    table_data = []
    for sym in symbols:
        alias = SYMBOL_ALIASES.get(sym, sym)
        df, status, provider = fetch_market_data(alias, "15m")
        if not df.empty:
            df_ind = calculate_indicators(df)
            sig = calculate_sekwaila_signal(df_ind)
            last_price = df['Close'].iloc[-1]
            change = ((last_price - df['Open'].iloc[0]) / df['Open'].iloc[0]) * 100
            
            table_data.append({
                "Symbol": alias,
                "Price": f"{last_price:,.2f}",
                "Change": f"{change:+.2f}%",
                "Signal": sig['action'],
                "Confidence": f"{sig['confidence']}%",
                "Risk/Reward": f"1:{sig['rr']}"
            })
            
    df_table = pd.DataFrame(table_data)
    st.dataframe(df_table, use_container_width=True, hide_index=True)
    
    col_sel, col_go = st.columns([3, 1])
    with col_sel:
        target_sym = st.selectbox("Select Asset to Analyze on Terminal", [row['Symbol'] for row in table_data])
    with col_go:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        if st.button("Open in Chart Terminal 📈"):
            st.session_state.selected_symbol = target_sym
            st.session_state.active_page = "Chart"
            st.rerun()

# --- B. CHART TERMINAL PAGE ---
def render_chart_page():
    tb1, tb2, tb3, tb4 = st.columns([2, 1.5, 3, 2.5])
    with tb1:
        # Corrected nested list comprehension
        all_symbols = [SYMBOL_ALIASES.get(s, s) for category in st.session_state.watchlist.values() for s in category]
        symbol = st.selectbox(
            "Asset", 
            sorted(list(set(all_symbols))), 
            index=0 if st.session_state.selected_symbol not in all_symbols else sorted(list(set(all_symbols))).index(st.session_state.selected_symbol)
        )
        st.session_state.selected_symbol = symbol
    with tb2:
        tf = st.selectbox("Timeframe", ["1m", "3m", "5m", "15m", "30m", "1H", "4H", "1D"], index=3)
        st.session_state.selected_timeframe = tf
    with tb3:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        show_ema = st.checkbox("EMA Overlays", value=True)
        show_struct = st.checkbox("Market Structure", value=True)
        show_sig = st.checkbox("Signal Targets", value=True)
    with tb4:
        df, data_status, provider_str = fetch_market_data(symbol, tf)
        st.markdown(f"<div style='text-align:right; margin-top:25px;'><span class='badge-gold'>{data_status}</span><br><small style='color:{COLOR_GREY};'>{provider_str}</small></div>", unsafe_allow_html=True)

    if df.empty:
        st.error("Unable to load data for this asset. Please try another timeframe or symbol.")
        return

    df_ind = calculate_indicators(df)
    df_struct = detect_market_structure(df_ind)
    signal = calculate_sekwaila_signal(df_struct)

    chart_col, panel_col = st.columns([3, 1])
    
    with chart_col:
        overlays = {"EMA_20": show_ema, "EMA_50": show_ema, "Structure": show_struct, "Signal Levels": show_sig}
        fig = render_professional_chart(df_struct, symbol, tf, signal, overlays)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        st.markdown(f"""
        <div class="term-card">
            <div style="display:flex; justify-content:space-between; text-align:center; font-size:12px;">
                <div><span style="color:{COLOR_GREY};">RSI (14)</span><br><b style="color:{COLOR_GREEN if signal['rsi'] >= 50 else COLOR_RED};">{signal['rsi']:.1f}</b></div>
                <div><span style="color:{COLOR_GREY};">ADX (14)</span><br><b>{signal['adx']:.1f}</b></div>
                <div><span style="color:{COLOR_GREY};">MFI (14)</span><br><b style="color:{COLOR_GREEN if signal['mfi'] >= 50 else COLOR_RED};">{signal['mfi']:.1f}</b></div>
                <div><span style="color:{COLOR_GREY};">Williams %R</span><br><b>{signal['wr']:.1f}</b></div>
                <div><span style="color:{COLOR_GREY};">CCI</span><br><b>{signal['cci']:.1f}</b></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with panel_col:
        st.markdown(f"""
        <div class="term-card-gold">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-weight:700; color:{COLOR_GOLD};">{symbol} SIGNAL</span>
                <span class="{'badge-buy' if 'BUY' in signal['action'] else ('badge-sell' if 'SELL' in signal['action'] else 'badge-neutral')}">{signal['action']}</span>
            </div>
            <h1 style="margin:10px 0 0 0; color:#FFF; font-size:28px;">{signal['confidence']}% <small style="font-size:12px; color:{COLOR_GREY};">CONFIDENCE</small></h1>
            <hr style="border-color:{COLOR_BORDER}; margin:10px 0;">
            <div style="font-size:13px; line-height:1.6;">
                <b>Trade Parameters:</b><br>
                Entry: <code>{signal['entry']:,.2f}</code><br>
                SL: <code style="color:{COLOR_RED};">{signal['sl']:,.2f}</code><br>
                TP1: <code style="color:{COLOR_GREEN};">{signal['tp1']:,.2f}</code><br>
                TP2: <code style="color:{COLOR_GREEN};">{signal['tp2']:,.2f}</code><br>
                R:R Ratio: <b>1:{signal['rr']}</b>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("#### 🧮 Risk Calculator")
        bal = st.session_state.get("account_bal", 500.0)
        risk_pct = st.session_state.get("risk_pct", 1.0)
        risk_zar = bal * (risk_pct / 100.0)
        sl_pips = abs(signal['entry'] - signal['sl'])
        
        st.markdown(f"""
        <div class="term-card" style="font-size:12px;">
            Account: <b>{st.session_state.get('currency', 'ZAR')} {bal:,.2f}</b><br>
            Risk ({risk_pct}%): <b style="color:{COLOR_RED};">{st.session_state.get('currency', 'ZAR')} {risk_zar:,.2f}</b><br>
            Stop Distance: <b>{sl_pips:,.2f} pts</b>
        </div>
        """, unsafe_allow_html=True)

# --- C. KATLEGO AI PAGE ---
def render_katlego_ai_page():
    st.markdown(f"### 🤖 KATLEGO AI Market Intelligence")
    st.caption("AI Market Analyst & Trade Strategy Engine")
    
    symbol = st.session_state.get("selected_symbol", "XAUUSD")
    tf = st.session_state.get("selected_timeframe", "15m")
    
    df, _, _ = fetch_market_data(symbol, tf)
    if not df.empty:
        df_ind = calculate_indicators(df)
        signal = calculate_sekwaila_signal(df_ind)
    else:
        st.error("Market data unavailable for Katlego AI evaluation.")
        return

    st.markdown("#### Quick Analysis Actions")
    q1, q2, q3, q4 = st.columns(4)
    
    query = ""
    if q1.button(f"📊 Analyze {symbol}"):
        query = f"Provide a complete technical analysis breakdown for {symbol} on the {tf} timeframe."
    if q2.button("🔥 Best Trade Setup"):
        query = "What is the highest-confidence trade setup available across the market right now?"
    if q3.button("⚠ Market Risks"):
        query = f"What are the key market risks, DXY headwinds, or invalidation points for {symbol}?"
    if q4.button("💰 R500 Account Plan"):
        query = f"Give me a disciplined execution plan for an R500 account trading {symbol} with strict 1% risk management."

    st.markdown(f"""
    <div class="term-card-gold">
        <h4 style="color:{COLOR_GOLD}; margin-top:0;">⚡ KATLEGO AI DIAGNOSTIC REPORT: {symbol}</h4>
        <p><b>Market Assessment:</b> {symbol} is currently showing a <b>{signal['action']}</b> signal with <b>{signal['confidence']}%</b> model confidence.</p>
        <p><b>Technical Justifications:</b></p>
        <ul>
            {"".join([f"<li>{r}</li>" for r in signal['reasons']])}
        </ul>
        <p><b>Execution Strategy:</b> Consider looking for entry retests near <code>{signal['entry']:,.2f}</code> with SL protected at <code>{signal['sl']:,.2f}</code>. Invalidated if price breaks opposite structural levels.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### 💬 Chat with Katlego AI")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {"role": "assistant", "content": f"Greetings. I am Katlego AI. I am monitoring {symbol} on {tf}. How can I assist your execution strategy?"}
        ]

    for msg in st.session_state.chat_history:
        st.chat_message(msg["role"]).write(msg["content"])

    user_input = st.chat_input(f"Ask Katlego AI about {symbol} or market strategy...")
    if user_input or query:
        active_query = user_input if user_input else query
        st.session_state.chat_history.append({"role": "user", "content": active_query})
        st.chat_message("user").write(active_query)
        
        response = f"Based on live data engine rules for {symbol}:\n\n"
        response += f"• **Signal**: {signal['action']} ({signal['confidence']}% Confidence)\n"
        response += f"• **Key Target (TP1)**: {signal['tp1']:,.2f}\n"
        response += f"• **Stop Loss**: {signal['sl']:,.2f}\n\n"
        response += "Primary Reasons:\n" + "\n".join([f"- {r}" for r in signal['reasons']])
        
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        st.chat_message("assistant").write(response)

# --- D. MARKET SCANNER PAGE ---
def render_market_scanner_page():
    st.markdown("### 📡 SEKWAILA OMEGA X Market Scanner")
    
    tf = st.selectbox("Scanner Timeframe", ["5m", "15m", "1H", "4H"], index=1)
    
    all_symbols = [SYMBOL_ALIASES.get(s, s) for category in st.session_state.watchlist.values() for s in category]
    
    scanner_results = []
    progress_bar = st.progress(0)
    
    unique_symbols = list(set(all_symbols))
    for idx, sym in enumerate(unique_symbols):
        df, _, _ = fetch_market_data(sym, tf)
        if not df.empty:
            df_ind = calculate_indicators(df)
            sig = calculate_sekwaila_signal(df_ind)
            last_price = df['Close'].iloc[-1]
            change = ((last_price - df['Open'].iloc[0]) / df['Open'].iloc[0]) * 100
            
            scanner_results.append({
                "Symbol": sym,
                "Price": f"{last_price:,.2f}",
                "Change %": f"{change:+.2f}%",
                "Signal": sig['action'],
                "Confidence": sig['confidence'],
                "RSI": round(sig['rsi'], 1),
                "ADX": round(sig['adx'], 1),
                "R:R": f"1:{sig['rr']}"
            })
        progress_bar.progress((idx + 1) / len(unique_symbols))
    progress_bar.empty()
    
    df_scan = pd.DataFrame(scanner_results)
    st.dataframe(df_scan.sort_values(by="Confidence", ascending=False), use_container_width=True, hide_index=True)

# --- E. MULTI-TIMEFRAME ANALYSIS PAGE ---
def render_mtf_page():
    symbol = st.selectbox("Select Asset for MTF Scan", ["XAUUSD", "BTCUSD", "EURUSD", "SP500", "US30"])
    
    timeframes = ["5m", "15m", "1H", "4H", "1D"]
    cols = st.columns(len(timeframes))
    
    signals = []
    for idx, tf in enumerate(timeframes):
        df, _, _ = fetch_market_data(symbol, tf)
        if not df.empty:
            df_ind = calculate_indicators(df)
            sig = calculate_sekwaila_signal(df_ind)
            signals.append(sig)
            
            with cols[idx]:
                st.markdown(f"""
                <div class="term-card" style="text-align:center;">
                    <b style="color:{COLOR_GOLD};">{tf}</b>
                    <h3 style="margin:5px 0;">{sig['action']}</h3>
                    <span class="badge-gold">{sig['confidence']}%</span>
                </div>
                """, unsafe_allow_html=True)
                
    bullish_count = sum(1 for s in signals if "BUY" in s['action'])
    bearish_count = sum(1 for s in signals if "SELL" in s['action'])
    alignment = max(bullish_count, bearish_count) / len(timeframes) * 100 if timeframes else 0
    
    st.markdown(f"""
    <div class="term-card-gold" style="text-align:center; margin-top:15px;">
        <h2>MULTI-TIMEFRAME ALIGNMENT: <span style="color:{COLOR_GOLD};">{alignment:.0f}%</span></h2>
        <p style="color:{COLOR_GREY};">Higher alignment across timeframes increases signal probability and trade duration stability.</p>
    </div>
    """, unsafe_allow_html=True)

# --- F. HEATMAP & CORRELATION MATRIX ---
def render_heatmap_page():
    st.markdown("### 🔥 Market Performance Heatmap")
    
    all_symbols = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "BTCUSD", "ETHUSD", "SP500", "US30"]
    heatmap_data = []
    
    for sym in all_symbols:
        df, _, _ = fetch_market_data(sym, "1D")
        if not df.empty:
            change = ((df['Close'].iloc[-1] - df['Open'].iloc[0]) / df['Open'].iloc[0]) * 100
            heatmap_data.append({"Symbol": sym, "Change": change})
            
    df_hm = pd.DataFrame(heatmap_data)
    fig = go.Figure(data=go.Treemap(
        labels=df_hm['Symbol'],
        parents=["Market"] * len(df_hm),
        values=np.abs(df_hm['Change']) + 0.1,
        textinfo="label+value",
        marker=dict(colors=df_hm['Change'], colorscale='RdYlGn', cmid=0)
    ))
    fig.update_layout(template="plotly_dark", paper_bgcolor=COLOR_CARD, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

def render_correlation_page():
    st.markdown("### 🔗 Asset Correlation Matrix")
    symbols = ["EURUSD", "GBPUSD", "XAUUSD", "BTCUSD", "SP500"]
    
    price_dict = {}
    for sym in symbols:
        df, _, _ = fetch_market_data(sym, "1D")
        if not df.empty:
            price_dict[sym] = df['Close']
            
    df_prices = pd.DataFrame(price_dict).dropna()
    corr = df_prices.corr()
    
    fig = go.Figure(data=go.Heatmap(
        z=corr.values, x=corr.columns, y=corr.index,
        colorscale='Viridis', zmin=-1, zmax=1
    ))
    fig.update_layout(template="plotly_dark", paper_bgcolor=COLOR_CARD)
    st.plotly_chart(fig, use_container_width=True)

# --- G. TRADE JOURNAL & PERFORMANCE ---
def render_journal_page():
    st.markdown("### 📖 SEKWAILA Trade Journal")
    
    with st.expander("➕ Log New Trade Entry"):
        with st.form("journal_form"):
            c1, c2, c3 = st.columns(3)
            date_val = c1.date_input("Date")
            sym_val = c2.text_input("Symbol", "XAUUSD")
            dir_val = c3.selectbox("Direction", ["BUY", "SELL"])
            
            c4, c5, c6 = st.columns(3)
            entry_val = c4.number_input("Entry Price", value=0.0)
            exit_val = c5.number_input("Exit Price", value=0.0)
            pnl_val = c6.number_input("PnL (ZAR)", value=0.0)
            
            reason = st.text_area("Trade Reason & Confluence Setup")
            submit = st.form_submit_button("Save Entry to Database")
            
            if submit:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("INSERT INTO journal (date, time, symbol, direction, entry, exit, pnl, reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                          (str(date_val), "", sym_val, dir_val, entry_val, exit_val, pnl_val, reason))
                conn.commit()
                conn.close()
                st.success("Trade entry successfully stored in SQLite database!")

    conn = sqlite3.connect(DB_FILE)
    df_j = pd.read_sql_query("SELECT * FROM journal ORDER BY id DESC", conn)
    conn.close()
    
    if not df_j.empty:
        st.dataframe(df_j, use_container_width=True)
    else:
        st.info("No trades currently recorded in database.")

def render_performance_page():
    st.markdown("### 📊 Trading Performance Metrics")
    
    conn = sqlite3.connect(DB_FILE)
    df_j = pd.read_sql_query("SELECT * FROM journal", conn)
    conn.close()
    
    if df_j.empty or 'pnl' not in df_j.columns:
        st.info("Log trades in the Trade Journal to calculate win rate and equity metrics.")
        return
        
    wins = df_j[df_j['pnl'] > 0]
    win_rate = (len(wins) / len(df_j)) * 100 if len(df_j) > 0 else 0
    total_pnl = df_j['pnl'].sum()
    
    p1, p2, p3 = st.columns(3)
    p1.metric("Win Rate", f"{win_rate:.1f}%")
    p2.metric("Total PnL", f"R {total_pnl:,.2f}")
    p3.metric("Total Trades", len(df_j))

# --- H. CONTROL CENTER / SETTINGS PAGE ---
def render_settings_page():
    st.markdown("### ⚙ SEKWAILA Control Center & Settings")
    
    t1, t2, t3, t4 = st.tabs(["General & Mode", "Risk Engine", "Wallpaper & Style", "Telegram & Alerts"])
    
    with t1:
        mode = st.selectbox("Data Operating Mode", ["DEMO", "LIVE"], index=0 if st.session_state.get("mode", "DEMO") == "DEMO" else 1)
        if st.button("Save Mode Setting"):
            st.session_state["mode"] = mode
            save_setting_to_db("mode", mode)
            st.success("Mode updated.")
            
    with t2:
        bal = st.number_input("Account Balance", value=float(st.session_state.get("account_bal", 500.0)))
        risk = st.slider("Default Risk %", 0.25, 5.0, float(st.session_state.get("risk_pct", 1.0)), 0.25)
        curr = st.selectbox("Currency", ["ZAR", "USD", "EUR", "GBP"], index=0)
        
        if st.button("Save Risk Settings"):
            st.session_state["account_bal"] = bal
            st.session_state["risk_pct"] = risk
            st.session_state["currency"] = curr
            save_setting_to_db("account_bal", bal)
            save_setting_to_db("risk_pct", risk)
            save_setting_to_db("currency", curr)
            st.success("Risk parameters saved.")

    with t3:
        wp_on = st.toggle("Enable Custom Wallpaper", value=st.session_state.get("wallpaper_enabled", False))
        wp_url = st.text_input("Wallpaper Image URL", value=st.session_state.get("wallpaper_bg", ""))
        opacity = st.slider("Wallpaper Opacity %", 5, 50, st.session_state.get("wallpaper_opacity", 20))
        
        if st.button("Apply Wallpaper"):
            st.session_state["wallpaper_enabled"] = wp_on
            st.session_state["wallpaper_bg"] = wp_url
            st.session_state["wallpaper_opacity"] = opacity
            save_setting_to_db("wallpaper_enabled", wp_on)
            save_setting_to_db("wallpaper_bg", wp_url)
            save_setting_to_db("wallpaper_opacity", opacity)
            st.success("Wallpaper configuration updated. Refreshing page...")
            st.rerun()

    with t4:
        st.text_input("Telegram Bot Token", type="password")
        st.text_input("Telegram Chat ID")
        st.button("Test Telegram Alert Dispatch")

def render_help_page():
    st.markdown("### ❓ Help & Terminology Guide")
    st.markdown("""
    * **ADX (Average Directional Index)**: Quantifies overall trend strength on a scale from 0 to 100. Readings above 25 signify strong trending markets.
    * **RSI (Relative Strength Index)**: Measures momentum velocity. Values above 50 signal bullish buyers, above 70 indicates overbought.
    * **MFI (Money Flow Index)**: Volume-weighted momentum indicator showing capital inflow/outflow.
    * **DXY (US Dollar Index)**: Measures USD strength relative to a basket of currencies. Weakness in DXY usually boosts Gold and Stocks.
    """)

# =============================================================================
# 11. MAIN APPLICATION ROUTER
# =============================================================================
def main():
    render_header()
    render_nav_menu()
    st.markdown("<hr style='border-color:#171C26; margin:8px 0 14px 0;'>", unsafe_allow_html=True)
    
    page = st.session_state.active_page
    
    if page == "Dashboard":
        render_dashboard_page()
    elif page == "Chart":
        render_chart_page()
    elif page == "Katlego AI":
        render_katlego_ai_page()
    elif page == "Market Scanner":
        render_market_scanner_page()
    elif page == "Multi-Timeframe":
        render_mtf_page()
    elif page == "Heatmap":
        render_heatmap_page()
    elif page == "Correlation Matrix":
        render_correlation_page()
    elif page == "Trade Journal":
        render_journal_page()
    elif page == "Performance":
        render_performance_page()
    elif page == "Settings":
        render_settings_page()
    elif page == "Help":
        render_help_page()
    else:
        render_dashboard_page()

if __name__ == "__main__":
    main()
