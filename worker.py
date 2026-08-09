"""
SEKWAILA OMEGA X — BACKGROUND WORKER ENGINE

Telegram uses the exact same generate_omega_signal()
as the Streamlit dashboard.
"""

import time

from config import (
    ASSETS,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    DEFAULT_MIN_TF_AGREEMENT,
    DEFAULT_MIN_SCORE,
    DEFAULT_MIN_RR,
    WORKER_POLL_SECONDS,
)

from engine import generate_omega_signal

from telegram_bot import send_telegram_message

from logger import get_logger


logger = get_logger("WORKER")


# Prevent identical alerts from being sent every polling cycle.
_last_alert_signature = {}


def _signal_signature(res):
    """
    Create a stable signature for the current actionable setup.
    """

    return (
        res.get("symbol"),
        res.get("bias"),
        round(float(res.get("entry", 0)), 4),
        round(float(res.get("stop", 0)), 4),
        round(float(res.get("tp2", 0)), 4),
        round(float(res.get("score", 0)), 1),
    )


def _build_alert_message(res):
    """
    Build Telegram message from the same engine result used by dashboard.
    """

    return (
        "👑 SEKWAILA OMEGA X ALERT\n"
        "\n"
        f"Asset: {res['symbol']}\n"
        f"Signal: {res['bias']}\n"
        f"Score: {res['score']}/100\n"
        f"Grade: {res['score'] >= 85 and 'A+' or ('A' if res['score'] >= 75 else 'B')}\n"
        "\n"
        f"Entry: {res['entry']:.4f}\n"
        f"Stop: {res['stop']:.4f}\n"
        f"TP1: {res['tp1']:.4f}\n"
        f"TP2: {res['tp2']:.4f}\n"
        f"TP3: {res['tp3']:.4f}\n"
        f"R:R: {res['rr']:.2f}\n"
        "\n"
        f"Structure: {res['structure']}\n"
        f"MTF: {res['bull_tf_count']} BUY / "
        f"{res['bear_tf_count']} SELL\n"
        f"RSI: {res['rsi']:.1f}\n"
        f"MACD: {res['macd_trend']}\n"
        f"ADX: {res['regime']['adx']}\n"
        f"Session: {res['session']}\n"
        f"Zone: {res['pd_zone']}\n"
        "\n"
        "⚠️ Rules-based informational alert."
    )


def run_worker():

    logger.info(
        "Starting SEKWAILA OMEGA X worker..."
    )

    if not TELEGRAM_BOT_TOKEN:
        logger.warning(
            "TELEGRAM_BOT_TOKEN is not configured."
        )

    if not TELEGRAM_CHAT_ID:
        logger.warning(
            "TELEGRAM_CHAT_ID is not configured."
        )

    while True:

        cycle_start = time.time()

        for symbol, ticker in ASSETS.items():

            try:

                logger.info(
                    f"Evaluating {symbol}..."
                )

                res = generate_omega_signal(
                    symbol,
                    ticker,
                    DEFAULT_MIN_TF_AGREEMENT,
                    DEFAULT_MIN_SCORE,
                    DEFAULT_MIN_RR,
                )

                if not res.get("ok"):

                    logger.warning(
                        f"{symbol}: "
                        f"{res.get('reason', 'Data unavailable')}"
                    )

                    continue

                logger.info(
                    f"{symbol}: "
                    f"{res['bias']} "
                    f"score={res['score']} "
                    f"RR={res['rr']}"
                )

                # ----------------------------------------------------------
                # Only actionable signals reach Telegram.
                # ----------------------------------------------------------

                if (
                    res["bias"]
                    not in ("BUY", "SELL")
                ):
                    continue

                if (
                    res["score"]
                    < DEFAULT_MIN_SCORE
                ):
                    continue

                if (
                    res["rr"]
                    < DEFAULT_MIN_RR
                ):
                    continue

                # ----------------------------------------------------------
                # Avoid duplicate alerts.
                # ----------------------------------------------------------

                signature = _signal_signature(
                    res
                )

                previous = (
                    _last_alert_signature.get(
                        symbol
                    )
                )

                if signature == previous:

                    logger.info(
                        f"{symbol}: "
                        "same signal already alerted."
                    )

                    continue

                # ----------------------------------------------------------
                # Telegram credentials check.
                # ----------------------------------------------------------

                if (
                    not TELEGRAM_BOT_TOKEN
                    or not TELEGRAM_CHAT_ID
                ):

                    logger.warning(
                        f"{symbol}: "
                        "Signal valid but Telegram credentials "
                        "are not configured."
                    )

                    _last_alert_signature[
                        symbol
                    ] = signature

                    continue

                message = _build_alert_message(
                    res
                )

                send_telegram_message(
                    TELEGRAM_BOT_TOKEN,
                    TELEGRAM_CHAT_ID,
                    message,
                )

                _last_alert_signature[
                    symbol
                ] = signature

                logger.info(
                    f"Dispatched new alert for {symbol}"
                )

            except Exception as exc:

                logger.exception(
                    f"Error evaluating {symbol}: {exc}"
                )

        elapsed = (
            time.time()
            - cycle_start
        )

        sleep_for = max(
            1,
            WORKER_POLL_SECONDS
            - int(elapsed),
        )

        logger.info(
            f"Scan complete. "
            f"Sleeping {sleep_for}s."
        )

        time.sleep(
            sleep_for
        )


if __name__ == "__main__":
    run_worker()
