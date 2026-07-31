import requests
import streamlit as st

BOT_TOKEN = st.secrets.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", "")


def send_alert(trade):

    if not BOT_TOKEN or not CHAT_ID:
        return

    message = f"""
{trade.signal}

{trade.symbol}

Confidence: {trade.confidence}%

Entry: {trade.entry:.2f}

Stop Loss: {trade.stop_loss:.2f}

TP1: {trade.tp1:.2f}
TP2: {trade.tp2:.2f}
TP3: {trade.tp3:.2f}

Reason:
{trade.reason}
"""

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    requests.post(
        url,
        json={
            "chat_id": CHAT_ID,
            "text": message
        },
        timeout=10
    )
