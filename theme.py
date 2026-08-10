"""
SEKWAILA OMEGA X — VISUAL SYSTEM

Design tokens
-------------
Background : #05070a (void) -> #0a0f16 (panel base), glass panels at 6% white
Hairline   : #1c2734
Text       : #e9eef5 (primary) / #7d8ba3 (dim) / #47536a (faint)
Signal hues:
  BUY      #22e6a3  (electric teal-green — not a generic acid green)
  SELL     #ff4d6a  (warm rose-red)
  NEUTRAL  #ffb238  (amber)
  EXTREME  intensified core-white + hue glow, pulsing
Type:
  Display  'Space Grotesk' — headers, badges
  Body     'Inter' — labels, prose
  Data     'JetBrains Mono' — every number (prices, scores, timestamps)
Signature: the pulse-glow ring on EXTREME-tier cards — a slow 2.4s heartbeat
that scales with how far the score sits above the EXTREME threshold, so the
glow itself is a legible signal (more urgent score -> faster/brighter pulse).
"""

import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;700&display=swap');

:root{
  --void:#05070a; --panel:#0a0f16; --panel2:#0d131b; --hair:#1c2734;
  --text:#e9eef5; --dim:#8592a8; --faint:#47536a;
  --buy:#22e6a3; --sell:#ff4d6a; --neutral:#ffb238;
  --buy-dim: rgba(34,230,163,.14); --sell-dim: rgba(255,77,106,.14); --neutral-dim: rgba(255,178,56,.12);
}

html, body, .stApp{
  background:
    radial-gradient(1200px 700px at 12% -10%, rgba(34,230,163,.05), transparent 60%),
    radial-gradient(1000px 600px at 100% 0%, rgba(255,77,106,.05), transparent 55%),
    repeating-linear-gradient(0deg, rgba(255,255,255,.014) 0px, rgba(255,255,255,.014) 1px, transparent 1px, transparent 34px),
    repeating-linear-gradient(90deg, rgba(255,255,255,.014) 0px, rgba(255,255,255,.014) 1px, transparent 1px, transparent 34px),
    var(--void);
  color: var(--text);
  font-family: 'Inter', sans-serif;
}
[data-testid="stSidebar"]{ background: var(--panel2); border-right:1px solid var(--hair); }
[data-testid="stHeader"]{ background: transparent; }
.block-container{ padding-top: 1.6rem; max-width: 1220px; }
h1,h2,h3{ font-family:'Space Grotesk', sans-serif !important; letter-spacing:.01em; }
::-webkit-scrollbar{ width:8px; height:8px; }
::-webkit-scrollbar-thumb{ background:#1c2734; border-radius:8px; }

/* ---------- header ---------- */
.omega-header{ display:flex; align-items:center; justify-content:space-between; gap:16px;
  padding:18px 22px; border:1px solid var(--hair); border-radius:16px;
  background: linear-gradient(135deg, rgba(255,255,255,.035), rgba(255,255,255,.01));
  margin-bottom: 22px; }
.omega-title{ font-family:'Space Grotesk',sans-serif; font-size:1.65rem; font-weight:700; letter-spacing:.02em; }
.omega-sub{ font-family:'JetBrains Mono',monospace; font-size:.72rem; color:var(--dim); letter-spacing:.12em; text-transform:uppercase; margin-top:2px;}
.status-row{ display:flex; gap:18px; align-items:center; font-family:'JetBrains Mono',monospace; font-size:.74rem; color:var(--dim); }
.dot{ width:8px; height:8px; border-radius:50%; display:inline-block; margin-right:6px; background:var(--buy);
  box-shadow:0 0 8px var(--buy); animation: blink 2s infinite; }
@keyframes blink{ 0%,100%{opacity:1;} 50%{opacity:.35;} }

/* ---------- nav ---------- */
.nav-crumb{ font-family:'JetBrains Mono',monospace; font-size:.75rem; color:var(--dim); margin-bottom:10px; }

/* ---------- signal cards ---------- */
.sig-card{ position:relative; border-radius:16px; padding:16px 18px; margin-bottom:12px;
  background: linear-gradient(160deg, rgba(255,255,255,.045), rgba(255,255,255,.012));
  border:1px solid var(--hair); overflow:hidden; }
.sig-card .top-row{ display:flex; justify-content:space-between; align-items:flex-start; }
.sig-symbol{ font-family:'Space Grotesk',sans-serif; font-size:1.15rem; font-weight:700; }
.sig-ticker{ font-family:'JetBrains Mono',monospace; font-size:.68rem; color:var(--faint); }
.sig-meta{ display:flex; gap:14px; margin-top:10px; font-family:'JetBrains Mono',monospace; font-size:.72rem; color:var(--dim); }
.badge{ font-family:'Space Grotesk',sans-serif; font-weight:700; font-size:.72rem; letter-spacing:.06em;
  padding:6px 12px; border-radius:999px; white-space:nowrap; }

/* tiers */
.badge.buy{ color:var(--buy); background:var(--buy-dim); border:1px solid rgba(34,230,163,.35); }
.badge.sell{ color:var(--sell); background:var(--sell-dim); border:1px solid rgba(255,77,106,.35); }
.badge.neutral{ color:var(--neutral); background:var(--neutral-dim); border:1px solid rgba(255,178,56,.3); }
.badge.unavailable{ color:var(--faint); background:rgba(255,255,255,.03); border:1px solid var(--hair); }

.sig-card.buy{ border-color:rgba(34,230,163,.28); box-shadow: inset 0 0 40px rgba(34,230,163,.03); }
.sig-card.sell{ border-color:rgba(255,77,106,.28); box-shadow: inset 0 0 40px rgba(255,77,106,.03); }
.sig-card.strong-buy{ border-color:rgba(34,230,163,.45); box-shadow: 0 0 22px rgba(34,230,163,.10), inset 0 0 40px rgba(34,230,163,.05); }
.sig-card.strong-sell{ border-color:rgba(255,77,106,.45); box-shadow: 0 0 22px rgba(255,77,106,.10), inset 0 0 40px rgba(255,77,106,.05); }
.sig-card.weak-buy{ border-color:rgba(34,230,163,.16); opacity:.88; }
.sig-card.weak-sell{ border-color:rgba(255,77,106,.16); opacity:.88; }
.sig-card.neutral{ opacity:.7; }
.sig-card.unavailable{ opacity:.55; border-style:dashed; }

.sig-card.extreme-buy{ border-color:#22e6a3; box-shadow: 0 0 30px rgba(34,230,163,.35), 0 0 70px rgba(34,230,163,.12), inset 0 0 50px rgba(34,230,163,.08);
  animation: pulse-buy 2.4s ease-in-out infinite; }
.sig-card.extreme-sell{ border-color:#ff4d6a; box-shadow: 0 0 30px rgba(255,77,106,.35), 0 0 70px rgba(255,77,106,.12), inset 0 0 50px rgba(255,77,106,.08);
  animation: pulse-sell 2.4s ease-in-out infinite; }
@keyframes pulse-buy{ 0%,100%{ box-shadow:0 0 30px rgba(34,230,163,.35),0 0 70px rgba(34,230,163,.12);} 50%{ box-shadow:0 0 46px rgba(34,230,163,.55),0 0 110px rgba(34,230,163,.22);} }
@keyframes pulse-sell{ 0%,100%{ box-shadow:0 0 30px rgba(255,77,106,.35),0 0 70px rgba(255,77,106,.12);} 50%{ box-shadow:0 0 46px rgba(255,77,106,.55),0 0 110px rgba(255,77,106,.22);} }
.badge.extreme-buy{ color:#04140d; background:linear-gradient(135deg,#22e6a3,#8dffdb); border:none; text-shadow:none; }
.badge.extreme-sell{ color:#1a0509; background:linear-gradient(135deg,#ff4d6a,#ffb0bf); border:none; }

/* ---------- generic panel / metric chip ---------- */
.panel{ border:1px solid var(--hair); border-radius:14px; padding:16px 18px;
  background:linear-gradient(160deg, rgba(255,255,255,.035), rgba(255,255,255,.008)); margin-bottom:14px; }
.panel h4{ font-family:'Space Grotesk',sans-serif; font-size:.82rem; letter-spacing:.09em; text-transform:uppercase;
  color:var(--dim); margin:0 0 12px 0; }
.chip-grid{ display:grid; grid-template-columns:repeat(auto-fit, minmax(120px,1fr)); gap:10px; }
.chip{ background:rgba(255,255,255,.025); border:1px solid var(--hair); border-radius:10px; padding:10px 12px; }
.chip .l{ font-family:'JetBrains Mono',monospace; font-size:.65rem; color:var(--faint); text-transform:uppercase; letter-spacing:.08em; }
.chip .v{ font-family:'JetBrains Mono',monospace; font-size:1.02rem; font-weight:700; margin-top:3px; }
.v.buy{ color:var(--buy); } .v.sell{ color:var(--sell); } .v.neutral{ color:var(--neutral); }

/* ---------- TF agreement bar ---------- */
.tf-row{ display:flex; align-items:center; justify-content:space-between; padding:9px 4px;
  border-bottom:1px solid var(--hair); font-family:'JetBrains Mono',monospace; font-size:.82rem; }
.tf-row:last-child{ border-bottom:none; }
.tf-label{ color:var(--dim); width:60px; }
.tf-pill{ font-weight:700; padding:3px 10px; border-radius:6px; font-size:.72rem; }
.tf-pill.buy{ color:var(--buy); background:var(--buy-dim);} .tf-pill.sell{ color:var(--sell); background:var(--sell-dim);} .tf-pill.neutral{ color:var(--neutral); background:var(--neutral-dim);}

/* dashboard grid: two cards per row on wide screens */
@media (min-width:900px){ .grid2{ column-count:2; column-gap:16px; } .grid2 > div{ break-inside: avoid; } }
</style>
"""


def inject():
    st.markdown(CSS, unsafe_allow_html=True)


def header(status_text: str, last_update: str, on_settings_key: str = "open_settings"):
    st.markdown(
        f"""
        <div class="omega-header">
          <div>
            <div class="omega-title">👑 SEKWAILA OMEGA X</div>
            <div class="omega-sub">LIVE MARKET INTELLIGENCE</div>
          </div>
          <div class="status-row">
            <span><span class="dot"></span>{status_text}</span>
            <span>LAST UPDATE&nbsp; {last_update}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def badge_html(level: str, css_class: str) -> str:
    return f'<span class="badge {css_class}">{level}</span>'


def metric_chip(label: str, value: str, css: str = "") -> str:
    return f'<div class="chip"><div class="l">{label}</div><div class="v {css}">{value}</div></div>'


def panel_open(title: str):
    st.markdown(f'<div class="panel"><h4>{title}</h4>', unsafe_allow_html=True)


def panel_close():
    st.markdown("</div>", unsafe_allow_html=True)
