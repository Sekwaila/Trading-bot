SEKWAILA OMEGA X — clean rebuild

BEFORE YOU DELETE ANYTHING
---------------------------
If database.py or trade_manager.py hold logic you care about, copy them
somewhere safe first. Neither is included here — I never saw their contents,
so nothing in this package touches them. Everything else in your old repo
is safe to delete, including:
  - engine.py (top-level, if it exists — this caused worker.py to import a
    file separate from the real engine)
  - data/market_data.py (the MT5-only, RSI-only fake engine with a second
    generate_omega_signal() and hardcoded 77%/65% confidence — this was a
    second competing engine, not part of your real system)
  - any capital-letter Signals/ folder (Streamlit Cloud is Linux — Signals
    and signals are two different folders to it, which is why one of your
    streamlit_app.py versions silently fell back to the wrong module)
  - the old streamlit_app.py that rendered "🔥 BUY NOW" cards from MT5 RSI

THE 11 FILES BELOW ARE THE WHOLE PROJECT
------------------------------------------
- streamlit_app.py         Entry point. Home (glowing signal cards, sorted
                            by strength), pair workspace, settings.
- theme.py                  Dark trading-terminal CSS + render helpers.
- classification.py         Labels the engine's own BUY/SELL/NEUTRAL with a
                            strength tier (EXTREME/STRONG/plain/WEAK) using
                            its own score + timeframe agreement + trend
                            output. Never overrides the engine's bias.
- settings_store.py         JSON-file-backed settings (General/Signals/Risk/
                            AI/Telegram/Data/Display), survives restarts.
- telegram_bot.py           send_telegram_message() + format_signal_message().
                            Used by BOTH the dashboard's Settings > Telegram
                            test button AND worker.py, so an alert and what
                            you see on screen can never disagree.
- worker.py                 Background poller — same engine, same message
                            formatter as the dashboard. Run with
                            `python worker.py`, or as the "worker" process
                            in the included Procfile.
- config.py                 All constants: assets, timeframes, thresholds,
                            classification tiers, contract sizes.
- logger.py
- signals/signal_engine.py  THE engine. Single source of truth for the
                            dashboard and worker. Nothing else defines
                            generate_omega_signal().
- signals/__init__.py
- requirements.txt          No MT5 dependency — runs identically on
                            Streamlit Cloud and locally, via yfinance.
- Procfile                  web + worker processes, if your host uses one.
- .streamlit/config.toml    Base dark theme so the terminal look holds even
                            before the injected CSS loads.

VERIFIED BEFORE DELIVERY
--------------------------
- Every .py file compiles (py_compile).
- Exactly one generate_omega_signal() definition in the whole project.
- No engine.py anywhere, any casing.
- No capitalized Signals/ folder — only lowercase signals/.
- classification.py / telegram_bot.py / settings_store.py functionally
  tested against a synthetic engine result (EXTREME BUY case, NEUTRAL case,
  DATA UNAVAILABLE case).
I could not fully launch Streamlit itself here (no network access in this
environment to install it) — run `streamlit run streamlit_app.py` locally
as your final check, and tell me anything that looks off.

Run locally:
    pip install -r requirements.txt
    streamlit run streamlit_app.py
    python worker.py     (separately, for Telegram alerts)
