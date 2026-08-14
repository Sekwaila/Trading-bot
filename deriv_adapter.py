"""
SEKWAILA OMEGA X
Deriv WebSocket Market Data Adapter

Provides:
- Live Deriv ticks
- Symbol conversion
- Connection testing
- Tick streaming

IMPORTANT:
Live trade execution is intentionally NOT enabled here.
"""

import os
import json
import asyncio
from typing import Optional, Dict, Any, Callable

import websockets

try:
    import streamlit as st
except Exception:
    st = None


# ============================================================
# SECRETS
# ============================================================

def get_secret(
    name: str,
    default: str = ""
) -> str:

    if st is not None:
        try:

            value = st.secrets.get(
                name,
                ""
            )

            if value:
                return str(value).strip()

        except Exception:
            pass

    return os.getenv(
        name,
        default
    ).strip()


DERIV_APP_ID = get_secret(
    "DERIV_APP_ID",
    "1089"
)

DERIV_API_TOKEN = (
    get_secret("DERIV_API_TOKEN")
    or
    get_secret("DERIV_API_KEY")
)

DERIV_WS_URL = (
    "wss://ws.derivws.com/websockets/v3"
    f"?app_id={DERIV_APP_ID}"
)


# ============================================================
# SYMBOL MAP
# ============================================================

SYMBOL_MAP = {

    "XAUUSD": "frxXAUUSD",

    "EURUSD": "frxEURUSD",

    "GBPUSD": "frxGBPUSD",

    "USDJPY": "frxUSDJPY",

    "USDCHF": "frxUSDCHF",

    "AUDUSD": "frxAUDUSD",

    "USDCAD": "frxUSDCAD",

    "BTCUSD": "cryBTCUSD",

    "ETHUSD": "cryETHUSD",

    "VOL10": "R_10",
    "VOL25": "R_25",
    "VOL50": "R_50",
    "VOL75": "R_75",
    "VOL100": "R_100",

    "BOOM1000": "1HZ1000V",
    "BOOM500": "1HZ500V",

    "CRASH1000": "1HZ1000S",
    "CRASH500": "1HZ500S",
}


def clean_symbol(
    symbol: str
) -> str:

    if not symbol:
        return ""

    clean = (
        symbol
        .replace("/", "")
        .replace("-", "")
        .strip()
        .upper()
    )

    return SYMBOL_MAP.get(
        clean,
        clean
    )


# ============================================================
# FETCH ONE PRICE
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
            DERIV_WS_URL,
            open_timeout=10,
            close_timeout=5,
        ) as ws:

            await ws.send(
                json.dumps(request)
            )

            response = await ws.recv()

            data = json.loads(response)

            if "tick" in data:

                quote = data["tick"].get(
                    "quote"
                )

                if quote is not None:
                    return float(quote)

            if "error" in data:

                print(
                    "[Deriv Error]",
                    data["error"].get(
                        "message",
                        "Unknown error"
                    )
                )

    except Exception as exc:

        print(
            "[Deriv Connection Error]",
            exc
        )

    return None


# ============================================================
# SYNCHRONOUS PRICE
# ============================================================

def get_deriv_price(
    symbol: str
) -> Optional[float]:

    try:

        return asyncio.run(
            fetch_deriv_price_async(
                symbol
            )
        )

    except RuntimeError:

        return None


# ============================================================
# LIVE TICK STREAM
# ============================================================

async def stream_ticks(
    symbol: str,
    callback: Callable[[float], None],
    duration_seconds: int = 60,
):

    deriv_symbol = clean_symbol(symbol)

    request = {
        "ticks": deriv_symbol,
        "subscribe": 1,
    }

    try:

        async with websockets.connect(
            DERIV_WS_URL
        ) as ws:

            await ws.send(
                json.dumps(request)
            )

            loop = asyncio.get_running_loop()

            start = loop.time()

            while (
                loop.time() - start
                < duration_seconds
            ):

                response = await ws.recv()

                data = json.loads(response)

                if "tick" not in data:
                    continue

                quote = data["tick"].get(
                    "quote"
                )

                if quote is None:
                    continue

                callback(
                    float(quote)
                )

    except Exception as exc:

        print(
            "[Deriv Stream Error]",
            exc
        )


# ============================================================
# CONNECTION TEST
# ============================================================

def test_deriv_connection(
    symbol: str = "XAUUSD"
) -> Dict[str, Any]:

    if not DERIV_APP_ID:

        return {
            "ok": False,
            "symbol": symbol,
            "deriv_symbol": None,
            "price": None,
            "error": (
                "DERIV_APP_ID is missing."
            ),
        }

    deriv_symbol = clean_symbol(symbol)

    price = get_deriv_price(symbol)

    if price is None:

        return {
            "ok": False,
            "symbol": symbol,
            "deriv_symbol": deriv_symbol,
            "price": None,
            "error": (
                "No Deriv tick received."
            ),
        }

    return {
        "ok": True,
        "symbol": symbol,
        "deriv_symbol": deriv_symbol,
        "price": price,
        "error": None,
    }


__all__ = [
    "clean_symbol",
    "get_deriv_price",
    "stream_ticks",
    "fetch_deriv_price_async",
    "test_deriv_connection",
]
