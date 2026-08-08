import base64
import datetime as dt
import hashlib
import json
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

try:
    import yfinance as yf
except ImportError:
    yf = None

st.set_page_config(page_title="SEKWAILA OMEGA X", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

ASSETS = {
    "XAUUSD": ("GC=F", "Gold / US Dollar", 2), "NAS100": ("NQ=F", "Nasdaq 100", 2),
    "US30": ("^DJI", "Dow Jones 30", 2), "SPX500": ("^GSPC", "S&P 500", 2),
    "BTCUSD": ("BTC-USD", "Bitcoin / US Dollar", 2), "EURUSD": ("EURUSD=X", "Euro / US Dollar", 5),
    "GBPUSD": ("GBPUSD=X", "Pound / US Dollar", 5), "USDJPY": ("JPY=X", "US Dollar / Yen", 3),
    "DXY": ("DX-Y.NYB", "US Dollar Index", 2),
}
TFS = ["15M", "1H", "4H", "1D"]
PRESETS = {
    "Obsidian Gold": "",
    "Ancestors": "https://images.unsplash.com/photo-1516026672322-bc52d61a55d5?auto=format&fit=crop&w=2400&q=85",
    "African Sunset": "https://images.unsplash.com/photo-1516426122078-c23e76319801?auto=format&fit=crop&w=2400&q=85",
    "Midnight": "",
}
DEFAULTS = {
    "watchlist": ["XAUUSD", "NAS100", "US30", "BTCUSD", "EURUSD", "GBPUSD", "USDJPY", "SPX500"],
    "min_conf": 65, "refresh": 60, "auto_refresh": False,
    "ema_fast": 20, "ema_slow": 50, "ema_trend": 200, "rsi_len": 14, "rsi_bull": 55, "rsi_bear": 45,
    "adx_len": 14, "adx_min": 20, "atr_len": 14, "bb_len": 20, "bb_std": 2.0, "mfi_len": 14, "stoch_len": 14,
    "use_ema": True, "use_rsi": True, "use_macd": True, "use_adx": True, "use_bb": True, "use_mfi": True,
    "use_stoch": True, "use_ichimoku": True, "use_supertrend": True, "use_structure": True,
    "use_liquidity": True, "use_fvg": True, "use_ob": True,
    "katlego": True, "katlego_style": "Institutional", "katlego_min": 65,
    "telegram": False, "telegram_token": "", "telegram_chat": "", "telegram_min": 75, "telegram_strong": True,
    "wallpaper": "Obsidian Gold", "wall_custom": "", "overlay": .82, "show_chart": True, "show_indicators": True,
    "account": 500.0, "risk": 1.0, "max_risk": 1.0,
}
for k,v in DEFAULTS.items(): st.session_state.setdefault(k,v)


def css():
    bg = st.session_state["wall_custom"] if st.session_state["wallpaper"] == "Custom" else PRESETS.get(st.session_state["wallpaper"], "")
    ov = st.session_state["overlay"]
    back = f'background-image:linear-gradient(rgba(4,6,9,{ov}),rgba(4,6,9,{ov})),url("{bg}");background-size:cover;background-position:center;background-attachment:fixed;' if bg else 'background:radial-gradient(circle at top,#1b1408 0%,#080a0f 48%,#040507 100%);'
    st.markdown(f'''<style>
    .stApp{{{back}color:#e9edf3}} [data-testid="stSidebar"]{{background:rgba(5,7,11,.95);border-right:1px solid #3b2c14}}
    .block-container{{max-width:1500px;padding:.45rem .8rem 1rem!important}} header{{visibility:hidden}} #MainMenu{{visibility:hidden}} footer{{visibility:hidden}}
    .title{{font-family:Georgia,serif;color:#f0c66a;text-align:center;letter-spacing:4px;font-size:clamp(30px,4vw,54px);margin:0}}
    .sub{{text-align:center;color:#b49a68;font-size:10px;letter-spacing:3px}}
    .card{{background:rgba(14,18,25,.90);border:1px solid rgba(217,164,65,.22);border-radius:12px;padding:14px;margin-bottom:12px;backdrop-filter:blur(6px)}}
    .gold{{color:#f0c66a!important}} .green{{color:#22c55e!important}} .red{{color:#ef4444!important}} .muted{{color:#8b95a7!important}}
    .buy{{background:linear-gradient(135deg,rgba(5,39,20,.94),rgba(7,14,10,.94));border:1px solid #22c55e;border-radius:14px;padding:17px}}
    .sell{{background:linear-gradient(135deg,rgba(53,8,10,.94),rgba(16,7,9,.94));border:1px solid #ef4444;border-radius:14px;padding:17px}}
    .neutral{{background:linear-gradient(135deg,rgba(48,37,12,.94),rgba(15,12,8,.94));border:1px solid #d9a441;border-radius:14px;padding:17px}}
    .pill{{padding:3px 8px;border-radius:999px;font-size:10px;font-weight:700}} .pb{{color:#4ade80;background:#0d2a18}} .ps{{color:#f87171;background:#321012}} .pn{{color:#f0c66a;background:#2b220e}}
    .metric{{background:rgba(20,25,34,.85);border:1px solid rgba(255,255,255,.06);border-radius:8px;padding:8px;text-align:center}} .ml{{font-size:9px;color:#8b95a7}} .mv{{font-size:17px;font-weight:700}}
    .section{{font-family:Georgia,serif;color:#f0c66a;letter-spacing:1px;font-size:16px;margin:4px 0 9px}}
    </style>''', unsafe_allow_html=True)
css()


def clean(df):
    if df is None or df.empty: return None
    if isinstance(df.columns,pd.MultiIndex): df.columns=df.columns.get_level_values(0)
    df.columns=[str(x).title() for x in df.columns]
    need=["Open","High","Low","Close"]
    if any(x not in df for x in need): return None
    for c in need+(["Volume"] if "Volume" in df else []): df[c]=pd.to_numeric(df[c],errors="coerce")
    return df.dropna(subset=need)

@st.cache_data(ttl=45,show_spinner=False)
def dl(ticker,period,interval):
    if yf is None:return None
    try:return clean(yf.download(ticker,period=period,interval=interval,auto_adjust=False,progress=False,threads=False))
    except Exception:return None

@st.cache_data(ttl=45,show_spinner=False)
def frames(ticker):
    d15=dl(ticker,"30d","15m"); d1=dl(ticker,"90d","1h"); dd=dl(ticker,"1y","1d")
    d4=None
    if d1 is not None and len(d1)>50:
        x=d1.copy()
        try:
            if getattr(x.index,"tz",None) is not None:x.index=x.index.tz_convert(None)
            d4=x.resample("4h").agg({"Open":"first","High":"max","Low":"min","Close":"last","Volume":"sum"}).dropna(subset=["Open","High","Low","Close"])
        except Exception: pass
    return {"15M":d15,"1H":d1,"4H":d4,"1D":dd}


def closed(df): return df.iloc[:-1].copy() if df is not None and len(df)>5 else None

def ema(s,n):return s.ewm(span=n,adjust=False).mean()
def atr(df,n):
    pc=df.Close.shift(); tr=pd.concat([df.High-df.Low,(df.High-pc).abs(),(df.Low-pc).abs()],axis=1).max(axis=1)
    return tr.ewm(alpha=1/n,adjust=False,min_periods=n).mean()
def rsi(s,n):
    d=s.diff();g=d.clip(lower=0);l=-d.clip(upper=0);ag=g.ewm(alpha=1/n,adjust=False).mean();al=l.ewm(alpha=1/n,adjust=False).mean();rs=ag/al.replace(0,np.nan);return 100-100/(1+rs)
def macd(s):
    m=ema(s,12)-ema(s,26); sig=ema(m,9);return m,sig,m-sig
def adx(df,n):
    up=df.High.diff();dn=-df.Low.diff();p=pd.Series(np.where((up>dn)&(up>0),up,0.),index=df.index);m=pd.Series(np.where((dn>up)&(dn>0),dn,0.),index=df.index)
    pc=df.Close.shift();tr=pd.concat([df.High-df.Low,(df.High-pc).abs(),(df.Low-pc).abs()],axis=1).max(axis=1);a=tr.ewm(alpha=1/n,adjust=False).mean();pdi=100*p.ewm(alpha=1/n,adjust=False).mean()/a;mdi=100*m.ewm(alpha=1/n,adjust=False).mean()/a;dx=100*(pdi-mdi).abs()/(pdi+mdi).replace(0,np.nan);return dx.ewm(alpha=1/n,adjust=False).mean()
def mfi(df,n):
    if "Volume" not in df or df.Volume.fillna(0).sum()==0:return pd.Series(np.nan,index=df.index)
    tp=(df.High+df.Low+df.Close)/3;money=tp*df.Volume.fillna(0);d=tp.diff();pos=money.where(d>0,0).rolling(n).sum();neg=money.where(d<0,0).abs().rolling(n).sum();mr=pos/neg.replace(0,np.nan);return 100-100/(1+mr)
def stoch(df,n):
    lo=df.Low.rolling(n).min();hi=df.High.rolling(n).max();k=100*(df.Close-lo)/(hi-lo).replace(0,np.nan);return k,k.rolling(3).mean()
def bb(s,n,std):
    m=s.rolling(n).mean();sd=s.rolling(n).std();return m,m+std*sd,m-std*sd
def ichi(df):
    t=(df.High.rolling(9).max()+df.Low.rolling(9).min())/2;k=(df.High.rolling(26).max()+df.Low.rolling(26).min())/2;a=(t+k)/2;b=(df.High.rolling(52).max()+df.Low.rolling(52).min())/2;return t,k,a,b

def swings(df,w=3):
    hi=df.High.rolling(2*w+1,center=True).max();lo=df.Low.rolling(2*w+1,center=True).min();return list(np.where((df.High==hi).fillna(False))[0]), list(np.where((df.Low==lo).fillna(False))[0])
def structure(df):
    sh,sl=swings(df)
    if len(sh)<2 or len(sl)<2:return "NEUTRAL","MIXED",None,None
    h1,h0=df.High.iloc[sh[-1]],df.High.iloc[sh[-2]];l1,l0=df.Low.iloc[sl[-1]],df.Low.iloc[sl[-2]];c=df.Close.iloc[-1]
    if c>h1:return "BUY","BULLISH BOS",float(h1),float(l1)
    if c<l1:return "SELL","BEARISH BOS",float(h1),float(l1)
    if h1>h0 and l1>l0:return "BUY","HH/HL",float(h1),float(l1)
    if h1<h0 and l1<l0:return "SELL","LH/LL",float(h1),float(l1)
    return "NEUTRAL","RANGE",float(h1),float(l1)
def sweep(df,n=20):
    if len(df)<n+3:return False,"NO SWEEP"
    r=df.iloc[-n-1:-1];b=df.iloc[-1]
    if b.Low<r.Low.min() and b.Close>r.Low.min():return True,"SELL-SIDE LIQUIDITY SWEPT"
    if b.High>r.High.max() and b.Close<r.High.max():return True,"BUY-SIDE LIQUIDITY SWEPT"
    return False,"NO SWEEP"
def fvg(df):
    out=None
    for i in range(max(2,len(df)-40),len(df)-1):
        if df.Low.iloc[i+1]>df.High.iloc[i-1]:out=("BULLISH FVG",float(df.High.iloc[i-1]),float(df.Low.iloc[i+1]))
        elif df.High.iloc[i+1]<df.Low.iloc[i-1]:out=("BEARISH FVG",float(df.High.iloc[i+1]),float(df.Low.iloc[i-1]))
    return out
def ob(df,bias):
    for i in range(len(df)-4,max(5,len(df)-60),-1):
        o,c,h,l=df.Open.iloc[i],df.Close.iloc[i],df.High.iloc[i],df.Low.iloc[i];q=df.iloc[i+1:i+4]
        if bias=="BUY" and c<o and q.High.max()>h*1.002:return ("BULLISH OB",float(l),float(h))
        if bias=="SELL" and c>o and q.Low.min()<l*.998:return ("BEARISH OB",float(l),float(h))
    return None


def snap(df):
    c=df.Close;ml,ms,mh=macd(c);k,d=stoch(df,st.session_state["stoch_len"]);bm,bu,bl=bb(c,st.session_state["bb_len"],st.session_state["bb_std"]);ta,ki,ia,ib=ichi(df)
    return {"price":float(c.iloc[-1]),"ema20":float(ema(c,st.session_state["ema_fast"]).iloc[-1]),"ema50":float(ema(c,st.session_state["ema_slow"]).iloc[-1]),"ema200":float(ema(c,st.session_state["ema_trend"]).iloc[-1]),"rsi":float(rsi(c,st.session_state["rsi_len"]).iloc[-1]),"adx":float(adx(df,st.session_state["adx_len"]).iloc[-1]),"atr":float(atr(df,st.session_state["atr_len"]).iloc[-1]),"macd":float(mh.iloc[-1]),"mfi":float(mfi(df,st.session_state["mfi_len"]).iloc[-1]) if pd.notna(mfi(df,st.session_state["mfi_len"]).iloc[-1]) else 50.,"stoch":float(k.iloc[-1]),"stochd":float(d.iloc[-1]),"bbmid":float(bm.iloc[-1]),"bbu":float(bu.iloc[-1]),"bbl":float(bl.iloc[-1]),"ia":float(ia.iloc[-1]),"ib":float(ib.iloc[-1])}

def analyze_tf(df,tf):
    if df is None or len(df)<80:return {"ok":False,"tf":tf}
    df=closed(df);x=snap(df);bias,struct,sh,sl=structure(df);sw,swt=sweep(df);gap=fvg(df);block=ob(df,bias)
    bull=bear=0.;reasons=[]
    def add(name,d,w):
        nonlocal bull,bear
        if d>0:bull+=w;reasons.append(("BUY",name))
        elif d<0:bear+=w;reasons.append(("SELL",name))
    if st.session_state["use_ema"]:add("EMA stack",1 if x["price"]>x["ema20"]>x["ema50"]>x["ema200"] else -1 if x["price"]<x["ema20"]<x["ema50"]<x["ema200"] else 0,1.2)
    if st.session_state["use_rsi"]:add("RSI",1 if x["rsi"]>=st.session_state["rsi_bull"] else -1 if x["rsi"]<=st.session_state["rsi_bear"] else 0,.8)
    if st.session_state["use_macd"]:add("MACD",1 if x["macd"]>0 else -1,.8)
    if st.session_state["use_adx"] and x["adx"]>=st.session_state["adx_min"]:add("ADX trend",1 if x["price"]>x["ema50"] else -1,.7)
    if st.session_state["use_bb"]:add("Bollinger",1 if x["price"]>x["bbmid"] else -1,.4)
    if st.session_state["use_mfi"]:add("MFI",1 if x["mfi"]>50 else -1,.4)
    if st.session_state["use_stoch"]:add("Stochastic",1 if x["stoch"]>x["stochd"] else -1,.35)
    if st.session_state["use_ichimoku"]:add("Ichimoku",1 if x["price"]>max(x["ia"],x["ib"]) else -1 if x["price"]<min(x["ia"],x["ib"]) else 0,.5)
    if st.session_state["use_structure"]:add(struct,1 if bias=="BUY" else -1 if bias=="SELL" else 0,1.3)
    if st.session_state["use_liquidity"] and sw:add(swt,1 if "SELL-SIDE" in swt else -1,.7)
    if st.session_state["use_fvg"] and gap:add(gap[0],1 if "BULLISH" in gap[0] else -1,.45)
    if st.session_state["use_ob"] and block:add(block[0],1 if "BULLISH" in block[0] else -1,.5)
    total=bull+bear;score=50 if total==0 else 50+50*(bull-bear)/total
    if x["adx"]<st.session_state["adx_min"]:score=50+(score-50)*.72
    score=float(np.clip(score,0,100));sig="STRONG BUY" if score>=75 else "BUY" if score>=65 else "STRONG SELL" if score<=25 else "SELL" if score<=35 else "NEUTRAL"
    return {"ok":True,"tf":tf,"score":round(score,1),"signal":sig,"ind":x,"structure":struct,"bias":bias,"sh":sh,"sl":sl,"sweep":sw,"sweep_text":swt,"fvg":gap,"ob":block,"reasons":reasons,"stamp":df.index[-1]}

def setting_hash():
    keys=[k for k in DEFAULTS if k.startswith("use_") or k in ["ema_fast","ema_slow","ema_trend","rsi_len","rsi_bull","rsi_bear","adx_len","adx_min","atr_len","bb_len","bb_std","mfi_len","stoch_len","min_conf"]]
    return hashlib.md5(json.dumps({k:st.session_state[k] for k in keys},sort_keys=True).encode()).hexdigest()

@st.cache_data(ttl=45,show_spinner=False)
def analyze_asset(asset,h):
    fs=frames(ASSETS[asset][0]);r={tf:analyze_tf(fs.get(tf),tf) for tf in TFS};valid=[v for v in r.values() if v.get("ok")]
    if not valid:return {"ok":False,"signal":"NO DATA","score":0,"timeframes":r}
    weights={"1D":2,"4H":1.6,"1H":1.3,"15M":1};score=sum(v["score"]*weights[t] for t,v in r.items() if v.get("ok"))/sum(weights[t] for t,v in r.items() if v.get("ok"));buys=sum(v["signal"] in ("BUY","STRONG BUY") for v in valid);sells=sum(v["signal"] in ("SELL","STRONG SELL") for v in valid)
    if buys>=3 and score>=st.session_state["min_conf"]:sig="STRONG BUY" if score>=75 else "BUY"
    elif sells>=3 and score<=100-st.session_state["min_conf"]:sig="STRONG SELL" if score<=25 else "SELL"
    else:sig="NEUTRAL"
    p=r.get("15M") if r.get("15M",{}).get("ok") else r.get("1H");x=p["ind"];entry=x["price"];av=max(x["atr"],entry*.001)
    if sig in ("BUY","STRONG BUY"):sl=min((p["sl"] or entry-1.5*av)-.15*av,entry-av);tp1=entry+1.5*av;tp2=entry+3*av;tp3=entry+5*av
    elif sig in ("SELL","STRONG SELL"):sl=max((p["sh"] or entry+1.5*av)+.15*av,entry+av);tp1=entry-1.5*av;tp2=entry-3*av;tp3=entry-5*av
    else:sl=entry-1.5*av;tp1=entry+1.5*av;tp2=entry+3*av;tp3=entry+5*av
    dist=abs(entry-sl);rr1=abs(tp1-entry)/dist if dist else 0;rr2=abs(tp2-entry)/dist if dist else 0
    regime="TRENDING / EXPANSION" if x["adx"]>=25 else "LOW-TREND / CHOP" if x["adx"]<18 else "DEVELOPING"
    reasons=[f"{t}: {v['signal']} {v['score']:.0f}% • {v['structure']}" for t,v in r.items() if v.get("ok")]
    if p.get("sweep"):reasons.append(p["sweep_text"])
    if p.get("fvg"):reasons.append(p["fvg"][0])
    if p.get("ob"):reasons.append(p["ob"][0])
    return {"ok":True,"signal":sig,"score":round(score,1),"entry":entry,"sl":sl,"tp1":tp1,"tp2":tp2,"tp3":tp3,"rr1":rr1,"rr2":rr2,"regime":regime,"primary":p,"timeframes":r,"reasons":reasons}

def ana(a):return analyze_asset(a,setting_hash())
def pf(a,x):return "—" if x is None or not np.isfinite(x) else f"{x:,.{ASSETS[a][2]}f}"
def pill(s):
    c="pb" if "BUY" in s else "ps" if "SELL" in s else "pn";return f"<span class='pill {c}'>{s}</span>"
def narrative(a,r):
    if not r.get("ok"):return f"Katlego: {a} has insufficient market data. No directional signal is issued."
    p=r["primary"];i=p["ind"];direction="bullish" if "BUY" in r["signal"] else "bearish" if "SELL" in r["signal"] else "mixed";extra="" if r["signal"]=="NEUTRAL" else f" The current setup is {r['signal']} with {r['score']:.0f}% heuristic confluence."
    return f"Katlego: {a} has a {direction} multi-timeframe bias. Structure is {p['structure']}, RSI is {i['rsi']:.1f}, ADX is {i['adx']:.1f}, and the regime is {r['regime'].lower()}.{extra} {p['sweep_text']}. I will not override a neutral engine state simply to force a trade."

def tg(token,chat,msg):
    if not token or not chat:return False,"Bot Token and Chat ID are required."
    try:
        q=urllib.parse.urlencode({"chat_id":chat,"text":msg});u=f"https://api.telegram.org/bot{token}/sendMessage?{q}"
        with urllib.request.urlopen(urllib.request.Request(u),timeout=12) as z:return z.status==200,"Telegram sent." if z.status==200 else z.read().decode()
    except Exception as e:return False,str(e)

def tgmsg(a,r):return f"⚡ SEKWAILA OMEGA X\nSIGNAL-ONLY ALERT\n\n{a} — {r['signal']}\nConfidence: {r['score']:.0f}%\nEntry: {pf(a,r['entry'])}\nTP1: {pf(a,r['tp1'])}\nTP2: {pf(a,r['tp2'])}\nTP3: {pf(a,r['tp3'])}\nSL: {pf(a,r['sl'])}\nR:R TP1: 1:{r['rr1']:.2f}\nRegime: {r['regime']}\n\nNo trade was executed."

# Sidebar
with st.sidebar:
    st.markdown("<div style='font-family:Georgia,serif;color:#f0c66a;font-size:23px;letter-spacing:2px'>⚡ SEKWAILA</div><div class='muted'>OMEGA X • SIGNAL-ONLY</div>",unsafe_allow_html=True)
    pages=["Dashboard","Market Scanner","Heatmap","AI Narrator","News Intelligence","Multi-Timeframe","Correlation Matrix","Trade Journal","Performance","Telegram Alerts","Settings","Help"]
    page=st.radio("MODULE",pages,label_visibility="collapsed")
    st.markdown("---")
    st.session_state["min_conf"]=st.slider("Minimum confidence",50,90,int(st.session_state["min_conf"]))
    st.session_state["refresh"]=st.slider("Refresh seconds",15,300,int(st.session_state["refresh"]),15)
    st.session_state["auto_refresh"]=st.toggle("Auto refresh",value=st.session_state["auto_refresh"])
    if st.button("🔄 Refresh data",use_container_width=True):st.cache_data.clear();st.rerun()
    st.caption("NO MT4/MT5 execution • NO broker orders")

st.markdown("<h1 class='title'>SEKWAILA OMEGA X</h1><div class='sub'>ANCIENT WISDOM • MODERN MARKET INTELLIGENCE • SIGNAL-ONLY</div>",unsafe_allow_html=True)
st.markdown("---")

if page=="Dashboard":
    st.markdown("<div class='section'>MARKET SIGNAL BOARD</div>",unsafe_allow_html=True)
    results={a:ana(a) for a in st.session_state["watchlist"]}
    html="<div class='card'><table style='width:100%;font-size:12px;border-collapse:collapse'><tr style='color:#a89265'><th align='left'>PAIR</th><th align='left'>SIGNAL</th><th>CONFIDENCE</th><th>PRICE</th><th>REGIME</th></tr>"
    for a,r in results.items():
        html+=f"<tr style='border-top:1px solid #1d222c'><td><b>{a}</b><br><span class='muted' style='font-size:9px'>{ASSETS[a][1]}</span></td><td>{pill(r['signal'])}</td><td align='center'>{r.get('score',0):.0f}%</td><td align='right'>{pf(a,r.get('entry'))}</td><td align='right'>{r.get('regime','—')}</td></tr>"
    st.markdown(html+"</table></div>",unsafe_allow_html=True)
    asset=st.selectbox("Open asset",st.session_state["watchlist"]);r=results[asset]
    if not r["ok"]:st.error("Market data unavailable. No signal generated.")
    else:
        cls="buy" if "BUY" in r["signal"] else "sell" if "SELL" in r["signal"] else "neutral"
        st.markdown(f"<div class='{cls}'><div style='display:flex;justify-content:space-between'><div><span class='gold'>{asset} • {ASSETS[asset][1]}</span><h2 style='margin:3px 0'>{r['signal']}</h2><span class='muted'>SIGNAL-ONLY • NO ORDER EXECUTION</span></div><div style='text-align:right'><span class='muted'>CONFLUENCE</span><div style='font-size:32px;font-weight:800'>{r['score']:.0f}%</div></div></div><hr style='border-color:#2c302f'><div style='display:grid;grid-template-columns:repeat(5,1fr);gap:8px;text-align:center'><div><span class='muted'>ENTRY</span><br><b>{pf(asset,r['entry'])}</b></div><div><span class='muted'>TP1</span><br><b class='green'>{pf(asset,r['tp1'])}</b></div><div><span class='muted'>TP2</span><br><b class='green'>{pf(asset,r['tp2'])}</b></div><div><span class='muted'>TP3</span><br><b class='green'>{pf(asset,r['tp3'])}</b></div><div><span class='muted'>STOP</span><br><b class='red'>{pf(asset,r['sl'])}</b></div></div></div>",unsafe_allow_html=True)
        c1,c2,c3=st.columns([1.5,1,1])
        with c1:
            st.markdown("<div class='section'>KATLEGO AI</div>",unsafe_allow_html=True);st.info(narrative(asset,r))
        with c2:
            st.markdown("<div class='section'>MULTI-TIMEFRAME</div>",unsafe_allow_html=True)
            for tf in TFS:
                x=r["timeframes"].get(tf);st.markdown(f"**{tf}** {pill(x['signal'])} {x['score']:.0f}%" if x and x.get('ok') else f"**{tf}** —",unsafe_allow_html=True)
        with c3:
            st.markdown("<div class='section'>RISK</div>",unsafe_allow_html=True);riskamt=st.session_state["account"]*st.session_state["risk"]/100;st.metric("Max planned risk",f"R{riskamt:.2f}");st.metric("TP1 R:R",f"1:{r['rr1']:.2f}");st.caption("Not broker lot sizing.")
        if st.session_state["show_chart"]:
            d=frames(ASSETS[asset][0])["15M"]
            if d is not None:
                d=d.tail(160);fig=go.Figure(go.Candlestick(x=d.index,open=d.Open,high=d.High,low=d.Low,close=d.Close,increasing_line_color="#22c55e",decreasing_line_color="#ef4444"));
                for y,name,col in [(r['entry'],'ENTRY','#d9a441'),(r['tp1'],'TP1','#22c55e'),(r['sl'],'SL','#ef4444')]:fig.add_hline(y=y,line_dash='dot',line_color=col,annotation_text=name)
                fig.update_layout(height=460,paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,.55)',font_color='#ddd',xaxis_rangeslider_visible=False,title=f"{asset} • 15M")
                st.plotly_chart(fig,use_container_width=True)
        if st.session_state["show_indicators"]:
            st.markdown("<div class='section'>INDICATORS</div>",unsafe_allow_html=True);i=r["primary"]["ind"];cols=st.columns(8);vals=[("RSI",i['rsi']),('ADX',i['adx']),('ATR',pf(asset,i['atr'])),('MACD',i['macd']),('MFI',i['mfi']),('STOCH',i['stoch']),('EMA','BULL' if i['price']>i['ema20']>i['ema50']>i['ema200'] else 'BEAR' if i['price']<i['ema20']<i['ema50']<i['ema200'] else 'MIXED'),('STRUCT',r['primary']['structure'])];
            for c,(k,v) in zip(cols,vals):c.markdown(f"<div class='metric'><div class='ml'>{k}</div><div class='mv'>{v:.1f}</div></div>" if isinstance(v,float) else f"<div class='metric'><div class='ml'>{k}</div><div class='mv'>{v}</div></div>",unsafe_allow_html=True)

elif page=="Market Scanner":
    st.markdown("<div class='section'>MARKET SCANNER</div>",unsafe_allow_html=True);rows=[]
    for a in st.session_state["watchlist"]:
        r=ana(a);rows.append({"Pair":a,"Signal":r["signal"],"Confidence":r.get("score",0),"Price":pf(a,r.get("entry")),"Regime":r.get("regime","UNAVAILABLE")})
    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)

elif page=="Heatmap":
    st.markdown("<div class='section'>MARKET HEATMAP</div>",unsafe_allow_html=True);rows=[]
    for a in st.session_state["watchlist"]:
        d=dl(ASSETS[a][0],"30d","1h")
        if d is not None and len(d)>3:
            c=closed(d);rows.append({"Asset":a,"Change":float((c.Close.iloc[-1]/c.Close.iloc[-2]-1)*100)})
    if rows:
        df=pd.DataFrame(rows);fig=px.treemap(df,path=['Asset'],values=df.Change.abs().replace(0,.01),color='Change',color_continuous_scale=['#ef4444','#171a20','#22c55e'],color_continuous_midpoint=0);fig.update_layout(paper_bgcolor='rgba(0,0,0,0)',font_color='#ddd');st.plotly_chart(fig,use_container_width=True)

elif page=="AI Narrator":
    st.markdown("<div class='section'>KATLEGO AI</div>",unsafe_allow_html=True);a=st.selectbox("Asset",st.session_state["watchlist"]);r=ana(a);st.markdown(f"<div class='card gold-card'><b class='gold'>KATLEGO • {st.session_state['katlego_style']}</b><br><br>{narrative(a,r)}</div>",unsafe_allow_html=True)
    if r.get('ok'):
        st.markdown("<div class='section'>EVIDENCE</div>",unsafe_allow_html=True)
        for x in r['reasons']:st.write('✓',x)
    q=st.chat_input("Ask Katlego…")
    if q:st.chat_message('user').write(q);st.chat_message('assistant').write(narrative(a,r))

elif page=="News Intelligence":
    st.markdown("<div class='section'>NEWS INTELLIGENCE</div>",unsafe_allow_html=True);st.warning("No fabricated news is used. For production live calendar/news intelligence, connect a licensed data provider.");st.info("The signal engine will not manufacture a macro event just to create a BUY/SELL call.")

elif page=="Multi-Timeframe":
    st.markdown("<div class='section'>MULTI-TIMEFRAME COMMAND CENTER</div>",unsafe_allow_html=True);a=st.selectbox('Asset',st.session_state['watchlist']);r=ana(a)
    for tf in TFS:
        x=r['timeframes'].get(tf);c1,c2,c3=st.columns([1,1,3]);c1.write(tf);c2.markdown(pill(x['signal'])+f" {x['score']:.0f}%" if x and x.get('ok') else '—',unsafe_allow_html=True);c3.write(f"{x['structure']} • RSI {x['ind']['rsi']:.1f} • ADX {x['ind']['adx']:.1f}" if x and x.get('ok') else 'Unavailable')

elif page=="Correlation Matrix":
    st.markdown("<div class='section'>LIVE CORRELATION MATRIX</div>",unsafe_allow_html=True);close={}
    for a in st.session_state['watchlist']:
        d=dl(ASSETS[a][0],'30d','1h')
        if d is not None:close[a]=d.Close
    if len(close)>=2:
        co=pd.DataFrame(close).pct_change().corr();fig=px.imshow(co,text_auto='.2f',zmin=-1,zmax=1,color_continuous_scale=['#ef4444','#171a20','#22c55e']);fig.update_layout(paper_bgcolor='rgba(0,0,0,0)',font_color='#ddd');st.plotly_chart(fig,use_container_width=True)

elif page=="Trade Journal":
    st.markdown("<div class='section'>SIGNAL JOURNAL</div>",unsafe_allow_html=True);st.session_state.setdefault('journal',[])
    with st.form('j'):
        a=st.selectbox('Pair',st.session_state['watchlist']);s=st.selectbox('Observed signal',['BUY','SELL','NEUTRAL']);n=st.text_area('Notes');ok=st.form_submit_button('Save observation')
    if ok:st.session_state['journal'].append({'Time':dt.datetime.now().isoformat(timespec='seconds'),'Pair':a,'Signal':s,'Notes':n});st.success('Saved.')
    if st.session_state['journal']:st.dataframe(pd.DataFrame(st.session_state['journal']),use_container_width=True,hide_index=True)

elif page=="Performance":
    st.markdown("<div class='section'>PERFORMANCE</div>",unsafe_allow_html=True);st.info('No fake win rate. Performance becomes meaningful after recorded signals have outcomes.');st.metric('Recorded observations',len(st.session_state.get('journal',[])))
    if st.session_state.get('journal'):st.dataframe(pd.DataFrame(st.session_state['journal']),use_container_width=True,hide_index=True)

elif page=="Telegram Alerts":
    st.markdown("<div class='section'>TELEGRAM SIGNAL CENTER</div>",unsafe_allow_html=True);st.session_state['telegram']=st.toggle('Enable Telegram',value=st.session_state['telegram']);st.session_state['telegram_token']=st.text_input('Bot Token',value=st.session_state['telegram_token'],type='password');st.session_state['telegram_chat']=st.text_input('Chat ID',value=st.session_state['telegram_chat']);st.session_state['telegram_min']=st.slider('Minimum confidence',50,95,int(st.session_state['telegram_min']));st.session_state['telegram_strong']=st.checkbox('Only STRONG signals',value=st.session_state['telegram_strong'])
    if st.button('Test Telegram'):
        ok,msg=tg(st.session_state['telegram_token'],st.session_state['telegram_chat'],'⚡ SEKWAILA OMEGA X Telegram test successful. SIGNAL-ONLY mode. No trade executed.');st.success(msg) if ok else st.error(msg)
    a=st.selectbox('Send current signal for',st.session_state['watchlist'])
    if st.button('Send current signal'):
        r=ana(a);allowed=r.get('ok') and r['score']>=st.session_state['telegram_min'] and (not st.session_state['telegram_strong'] or r['signal'] in ('STRONG BUY','STRONG SELL'))
        if not allowed:st.warning('Signal does not meet Telegram filters. Nothing sent.')
        else:
            ok,msg=tg(st.session_state['telegram_token'],st.session_state['telegram_chat'],tgmsg(a,r));st.success(msg) if ok else st.error(msg)

elif page=="Settings":
    st.markdown("<div class='section'>OMEGA X SETTINGS CENTER</div>",unsafe_allow_html=True);tabs=st.tabs(['General','Indicators','SMC','Katlego AI','Telegram','Appearance','Risk & Safety','Data'])
    with tabs[0]:
        st.session_state['watchlist']=st.multiselect('Dashboard pairs',list(ASSETS),default=st.session_state['watchlist']);st.session_state['min_conf']=st.slider('Minimum signal confidence',50,90,int(st.session_state['min_conf']));st.session_state['refresh']=st.slider('Refresh seconds',15,300,int(st.session_state['refresh']),15);st.session_state['auto_refresh']=st.toggle('Auto refresh',value=st.session_state['auto_refresh'])
    with tabs[1]:
        a,b,c=st.columns(3)
        with a:st.session_state['ema_fast']=st.number_input('EMA Fast',5,100,int(st.session_state['ema_fast']));st.session_state['rsi_len']=st.number_input('RSI Length',5,50,int(st.session_state['rsi_len']));st.session_state['adx_len']=st.number_input('ADX Length',5,50,int(st.session_state['adx_len']));st.session_state['atr_len']=st.number_input('ATR Length',5,50,int(st.session_state['atr_len']))
        with b:st.session_state['ema_slow']=st.number_input('EMA Slow',10,200,int(st.session_state['ema_slow']));st.session_state['rsi_bull']=st.slider('RSI Bull threshold',50,70,int(st.session_state['rsi_bull']));st.session_state['adx_min']=st.slider('ADX minimum',10,40,int(st.session_state['adx_min']));st.session_state['bb_len']=st.number_input('BB Length',5,100,int(st.session_state['bb_len']))
        with c:st.session_state['ema_trend']=st.number_input('EMA Trend',50,400,int(st.session_state['ema_trend']));st.session_state['rsi_bear']=st.slider('RSI Bear threshold',30,50,int(st.session_state['rsi_bear']));st.session_state['mfi_len']=st.number_input('MFI Length',5,50,int(st.session_state['mfi_len']));st.session_state['stoch_len']=st.number_input('Stoch Length',5,50,int(st.session_state['stoch_len']))
        st.session_state['bb_std']=st.number_input('BB Std Dev',1.,4.,float(st.session_state['bb_std']),.1)
        labels=[('use_ema','EMA'),('use_rsi','RSI'),('use_macd','MACD'),('use_adx','ADX'),('use_bb','Bollinger'),('use_mfi','MFI'),('use_stoch','Stochastic'),('use_ichimoku','Ichimoku')]
        for k,l in labels:st.session_state[k]=st.checkbox(l,value=st.session_state[k])
    with tabs[2]:
        st.session_state['use_structure']=st.checkbox('BOS / market structure',value=st.session_state['use_structure']);st.session_state['use_liquidity']=st.checkbox('Liquidity sweeps',value=st.session_state['use_liquidity']);st.session_state['use_fvg']=st.checkbox('Fair Value Gaps',value=st.session_state['use_fvg']);st.session_state['use_ob']=st.checkbox('Order Blocks',value=st.session_state['use_ob']);st.info('SMC evidence is heuristic; it does not prove institutional order flow.')
    with tabs[3]:
        st.session_state['katlego']=st.toggle('Enable Katlego',value=st.session_state['katlego']);st.session_state['katlego_style']=st.selectbox('Style',['Institutional','Concise','Coach','Aggressive'],index=['Institutional','Concise','Coach','Aggressive'].index(st.session_state['katlego_style']));st.session_state['katlego_min']=st.slider('Strong-language threshold',50,95,int(st.session_state['katlego_min']));st.info('Katlego narrates the OMEGA X evidence. It does not fabricate a directional call.')
    with tabs[4]:
        st.session_state['telegram']=st.toggle('Enable Telegram',value=st.session_state['telegram']);st.session_state['telegram_token']=st.text_input('Bot Token',value=st.session_state['telegram_token'],type='password');st.session_state['telegram_chat']=st.text_input('Chat ID',value=st.session_state['telegram_chat']);st.session_state['telegram_min']=st.slider('Alert minimum',50,95,int(st.session_state['telegram_min']));st.session_state['telegram_strong']=st.checkbox('Only strong signals',value=st.session_state['telegram_strong']);st.warning('Use Streamlit secrets for production bot tokens.')
    with tabs[5]:
        opts=list(PRESETS)+['Custom'];st.session_state['wallpaper']=st.selectbox('Wallpaper',opts,index=opts.index(st.session_state['wallpaper']) if st.session_state['wallpaper'] in opts else 0);st.session_state['overlay']=st.slider('Wallpaper darkness',.35,.95,float(st.session_state['overlay']),.01)
        if st.session_state['wallpaper']=='Custom':
            up=st.file_uploader('Upload ancestor wallpaper',type=['png','jpg','jpeg','webp'])
            if up:
                st.session_state['wall_custom']=f"data:{up.type};base64,{base64.b64encode(up.getvalue()).decode()}"
        st.session_state['show_chart']=st.checkbox('Show chart',value=st.session_state['show_chart']);st.session_state['show_indicators']=st.checkbox('Show indicators',value=st.session_state['show_indicators']);st.button('Apply appearance',on_click=st.rerun)
    with tabs[6]:
        st.session_state['account']=st.number_input('Account balance (R)',0.,10000000.,float(st.session_state['account']),50.);st.session_state['max_risk']=st.slider('Maximum risk setting %',.1,5.,float(st.session_state['max_risk']),.1);st.session_state['risk']=min(st.slider('Default risk %',.1,5.,float(st.session_state['risk']),.1),st.session_state['max_risk']);st.error('AUTO-TRADING IS PERMANENTLY DISABLED.')
    with tabs[7]:
        st.write('Market data: Yahoo Finance via yfinance. Intraday availability depends on provider.');st.write('The engine refuses directional output when required data is unavailable.');
        if yf is None:st.error('Install yfinance.');
        else:st.success('yfinance available.');
        if st.button('Clear market cache'):st.cache_data.clear();st.success('Cache cleared.')

elif page=="Help":
    st.markdown("<div class='section'>HELP & GUIDE</div>",unsafe_allow_html=True);st.markdown('''### Dashboard
Clean pair/signal board first, then deep analysis after selecting an asset.

### Indicators
EMA, RSI, MACD, ADX, ATR, Bollinger, MFI, Stochastic and Ichimoku can be enabled/disabled.

### SMC
BOS/structure, liquidity sweeps, FVG and Order Blocks feed the confluence model.

### Katlego
Katlego explains the engine evidence and does not override NEUTRAL states.

### Telegram
Telegram is notification-only. It cannot execute broker orders.

### Appearance
Choose ancestor wallpapers or upload your own in Settings → Appearance.

### Safety
There is no MT4/MT5 execution module in this application.''')

if st.session_state['auto_refresh']:
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=st.session_state['refresh']*1000,key='omega_refresh')
    except Exception: st.caption('Install streamlit-autorefresh for automatic refresh.')

st.markdown("---")
st.markdown("<div style='text-align:center;color:#766647;font-size:10px;letter-spacing:1px'>SEKWAILA OMEGA X • SIGNAL-ONLY • NO AUTOMATIC TRADE EXECUTION • HEURISTIC ANALYSIS, NOT FINANCIAL ADVICE</div>",unsafe_allow_html=True)
