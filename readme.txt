SEKWAILA OMEGA X - Deriv live feed + Telegram alert worker edition

Files:
- streamlit_app.py       (dashboard)
- worker.py              (background Telegram alert scanner)
- config.py
- logger.py
- signals/signal_engine.py
- signals/__init__.py
- requirements.txt
- Procfile               (tells Railway how to run both processes)

PRICE FEED:
Live prices come from Deriv's free WebSocket API. yfinance is kept only
for USD/ZAR conversion (position sizing) and the optional correlation
matrix.

TELEGRAM ALERTS WHILE YOU'RE AWAY FROM THE SCREEN:
worker.py is a separate, always-on process. It scans every asset in
config.ASSETS on a loop (every WORKER_POLL_SECONDS, default 300s = 5 min)
and sends a Telegram message only when a NEW BUY/SELL signal appears on
a symbol -- it will not spam you every poll cycle for the same signal.

DEPLOYING BOTH PROCESSES ON RAILWAY:
Railway needs to run streamlit_app.py and worker.py as two separate
services from the same repo, because they're independent long-running
processes:

  1. Deploy the repo as normal -- this becomes your "web" service
     (dashboard), using the Procfile's "web" line automatically if
     Railway detects it, or set the start command manually to:
     streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0

  2. In the same Railway project, click "+ New" -> "Empty Service" (or
     "GitHub Repo" again) and point it at the SAME repo/branch.

  3. On that second service, go to Settings -> set the Start Command to:
     python worker.py
     (This is the "worker" line in the Procfile.)

  4. Copy ALL the same environment variables to BOTH services:
     DERIV_API_TOKEN, DERIV_APP_ID (optional), TELEGRAM_BOT_TOKEN,
     TELEGRAM_CHAT_ID. The worker specifically needs TELEGRAM_BOT_TOKEN
     and TELEGRAM_CHAT_ID to send messages, and DERIV_API_TOKEN to read
     prices.

  5. Deploy the worker service. Check its logs for:
     "SEKWAILA OMEGA X worker starting..." and a Telegram message
     should arrive confirming it's live.

Once both services are running, the worker keeps scanning and alerting
24/7 even with your phone locked or the dashboard closed -- exactly like
your existing Telegram bot setup, just now reading real Deriv prices.

REMINDER: Deriv API tokens expire (default ~90 days). When it expires,
BOTH the dashboard and the worker will stop getting live prices until
you regenerate the token in Deriv and update DERIV_API_TOKEN on both
Railway services.
