"""
SEKWAILA OMEGA X
Deriv market-data adapter.

Provides:
- Deriv connection test
- Latest tick
- Live tick subscription
- Symbol mapping

LIVE TRADE EXECUTION IS DISABLED IN THIS VERSION.
"""

import os
import json
import asyncio
from typing import Optional, Dict, Any, Callable

import websockets


# ============================================================
# CONFIGURATION
# ============================================================

def get_deriv_app_id() -> str:

    try:
        import streamlit as st

        app_id = st.secrets.get(
            "DERIV_APP_ID",
            "1089"
        )

        return str(app_id).strip()

    except Exception:
        return os.getenv(
            "DERIV_APP_ID",
            "1089"
        ).strip()


def get_deriv_token() -> str:

    try:
        import streamlit as st

        token = st.secrets.get(
            "DERIV_API_TOKEN",
            ""
        )

        return str(token).strip()

    except Exception:
        return os.getenv(
            "DERIV_API_TOKEN",
            ""
        ).strip()


def get_ws_url() -> str:

    app_id = get_deriv_app_id()

    return (
        "wss://ws.derivws.com/websockets/v3"
        f"?app_id={app_id}"
    )


# ============================================================
# SYMBOL MAP
# ============================================================

SYMBOL_MAP = {

    # Forex
    "EURUSD": "frxEURUSD",
    "GBPUSD": "frxGBPUSD",
    "USDJPY": "frxUSDJPY",
    "AUDUSD": "frxAUDUSD",
    "USDCAD": "frxUSDCAD",
    "USDCHF": "frxUSDCHF",
    "NZDUSD": "frxNZDUSD",

    # Gold
    "XAUUSD": "frxXAUUSD",

    # Crypto
    "BTCUSD": "cryBTCUSD",
    "ETHUSD": "cryETHUSD",

    # Volatility indices
    "VOL10": "R_10",
    "VOL25": "R_25",
    "VOL50": "R_50",
    "VOL75": "R_75",
    "VOL100": "R_100",

    # 1-second volatility
    "VOL10_1S": "1HZ10V",
    "VOL25_1S": "1HZ25V",
    "VOL50_1S": "1HZ50V",
    "VOL75_1S": "1HZ75V",
    "VOL100_1S": "1HZ100V",

    # Boom / Crash
    "BOOM300": "BOOM300",
    "BOOM500": "BOOM500",
    "BOOM1000": "BOOM1000",

    "CRASH300": "CRASH300",
    "CRASH500": "CRASH500",
    "CRASH1000": "CRASH1000",
}


def clean_symbol(symbol: str) -> str:

    if not symbol:
        return ""

    clean = (
        str(symbol)
        .replace("/", "")
        .replace(" ", "")
        .upper()
        .strip()
    )

    return SYMBOL_MAP.get(
        clean,
        clean
    )


# ============================================================
# ASYNC LATEST PRICE
# ============================================================

async def fetch_deriv_price_async(
    symbol: str
) -> Optional[float]:

    deriv_symbol = clean_symbol(symbol)

    if not deriv_symbol:
        return None

    request = {
        "ticks": deriv_symbol
    }

    try:

        async with websockets.connect(
            get_ws_url(),
            open_timeout=10,
            close_timeout=5,
            ping_interval=20,
            ping_timeout=20,
        ) as ws:

            await ws.send(
                json.dumps(request)
            )

            response = await ws.recv()

            data = json.loads(response)

            if "error" in data:

                print(
                    "[Deriv Error]",
                    data["error"].get(
                        "message",
                        "Unknown Deriv error"
                    )
                )

                return None

            tick = data.get("tick")

            if not tick:
                return None

            quote = tick.get("quote")

            if quote is None:
                return None

            return float(quote)

    except Exception as exc:

        print(
            f"[Deriv Price Error] {symbol}: {exc}"
        )

        return None


# ============================================================
# SYNC PRICE
# ============================================================

def get_deriv_price(
    symbol: str
) -> Optional[float]:

    try:
        return asyncio.run(
            fetch_deriv_price_async(symbol)
        )

    except RuntimeError:

        # Streamlit / running event loop fallback
        try:

            loop = asyncio.new_event_loop()

            try:
                return loop.run_until_complete(
                    fetch_deriv_price_async(symbol)
                )

            finally:
                loop.close()

        except Exception as exc:

            print(
                f"[Deriv Loop Error] {exc}"
            )

            return None

    except Exception as exc:

        print(
            f"[Deriv Sync Error] {exc}"
        )

        return None


# ============================================================
# LIVE TICK STREAM
# ============================================================

async def stream_ticks(
    symbol: str,
    callback: Callable[[float], None],
    duration_seconds: int = 60
):

    deriv_symbol = clean_symbol(symbol)

    if not deriv_symbol:
        return

    request = {
        "ticks": deriv_symbol,
        "subscribe": 1,
    }

    try:

        async with websockets.connect(
            get_ws_url(),
            open_timeout=10,
            close_timeout=5,
            ping_interval=20,
            ping_timeout=20,
        ) as ws:

            await ws.send(
                json.dumps(request)
            )

            loop = asyncio.get_running_loop()

            start_time = loop.time()

            while (
                loop.time() - start_time
                < duration_seconds
            ):

                response = await ws.recv()

                data = json.loads(response)

                if "error" in data:

                    print(
                        "[Deriv Stream Error]",
                        data["error"].get(
                            "message",
                            "Unknown error"
                        )
                    )

                    break

                tick = data.get("tick")

                if not tick:
                    continue

                quote = tick.get("quote")

                if quote is None:
                    continue

                try:
                    callback(float(quote))

                except Exception as callback_error:

                    print(
                        "[Deriv Callback Error]",
                        callback_error
                    )

    except Exception as exc:

        print(
            f"[Deriv Stream Error] {symbol}: {exc}"
        )


# ============================================================
# CONNECTION TEST
# ============================================================

def test_deriv_connection(
    symbol: str = "XAUUSD"
) -> Dict[str, Any]:

    app_id = get_deriv_app_id()

    if not app_id:

        return {
            "connected": False,
            "message": "DERIV_APP_ID is missing."
        }

    price = get_deriv_price(symbol)

    if price is None:

        return {
            "connected": False,
            "message": (
                f"No Deriv tick received for "
                f"{symbol}."
            )
        }

    return {
        "connected": True,
        "symbol": clean_symbol(symbol),
        "price": price,
        "message": "Deriv market data connected."
    }


# ============================================================
# LIVE EXECUTION
# ============================================================

def execute_deriv_trade(
    symbol: str,
    direction: str,
    stake_amount: float = 10.0
) -> Dict[str, Any]:

    return {
        "status": "disabled",
        "message": (
            "Live Deriv execution is disabled. "
            "Verify market-data connections first."
        ),
        "symbol": clean_symbol(symbol),
        "direction": direction,
        "stake": stake_amount,
    }


__all__ = [
    "get_deriv_price",
    "fetch_deriv_price_async",
    "stream_ticks",
    "test_deriv_connection",
    "clean_symbol",
    "execute_deriv_trade",
]
