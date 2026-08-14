"""
SEKWAILA OMEGA X
Deriv market-data adapter.

IMPORTANT:
This module currently handles PUBLIC MARKET DATA ONLY.

It does NOT place trades.

Deriv public tick data does not require a trading token.
"""

from __future__ import annotations

import asyncio
import json
from typing import Optional, Callable

import websockets


# Deriv's public WebSocket endpoint for the legacy/general market-data API.
DERIV_WS_URL = "wss://ws.binaryws.com/websockets/v3"


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

    # Synthetic indices
    "VOL10": "R_10",
    "VOL25": "R_25",
    "VOL50": "R_50",
    "VOL75": "R_75",
    "VOL100": "R_100",

    "BOOM300": "BOOM300",
    "BOOM500": "BOOM500",
    "BOOM1000": "BOOM1000",

    "CRASH300": "CRASH300",
    "CRASH500": "CRASH500",
    "CRASH1000": "CRASH1000",

    # High-frequency volatility
    "1HZ10V": "1HZ10V",
    "1HZ25V": "1HZ25V",
    "1HZ50V": "1HZ50V",
    "1HZ75V": "1HZ75V",
    "1HZ100V": "1HZ100V",
}


def clean_symbol(symbol: str) -> str:
    if not symbol:
        return ""

    clean = (
        str(symbol)
        .upper()
        .replace("/", "")
        .replace(" ", "")
        .strip()
    )

    return SYMBOL_MAP.get(clean, clean)


async def fetch_deriv_price_async(
    symbol: str,
) -> Optional[float]:

    deriv_symbol = clean_symbol(symbol)

    if not deriv_symbol:
        return None

    request = {
        "ticks": deriv_symbol,
        "subscribe": 0,
    }

    try:
        async with websockets.connect(
            DERIV_WS_URL,
            open_timeout=10,
            close_timeout=5,
            ping_interval=20,
            ping_timeout=20,
        ) as ws:

            await ws.send(json.dumps(request))

            raw = await asyncio.wait_for(
                ws.recv(),
                timeout=10,
            )

            data = json.loads(raw)

            if data.get("error"):
                print(
                    "[Deriv]",
                    data["error"].get(
                        "message",
                        "Unknown Deriv error",
                    ),
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
            f"[Deriv price error] "
            f"{symbol}: {exc}"
        )
        return None


def get_deriv_price(
    symbol: str,
) -> Optional[float]:

    try:
        return asyncio.run(
            fetch_deriv_price_async(symbol)
        )

    except RuntimeError:
        # Streamlit may already have an event loop.
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
                f"[Deriv loop error] {exc}"
            )
            return None

    except Exception as exc:
        print(
            f"[Deriv wrapper error] {exc}"
        )
        return None


async def stream_ticks(
    symbol: str,
    callback: Callable[[float], None],
    duration_seconds: int = 60,
):
    """
    Stream public Deriv ticks for a limited duration.
    """

    deriv_symbol = clean_symbol(symbol)

    if not deriv_symbol:
        return

    request = {
        "ticks": deriv_symbol,
        "subscribe": 1,
    }

    try:
        async with websockets.connect(
            DERIV_WS_URL,
            open_timeout=10,
            close_timeout=5,
            ping_interval=20,
            ping_timeout=20,
        ) as ws:

            await ws.send(json.dumps(request))

            loop = asyncio.get_running_loop()
            start = loop.time()

            while loop.time() - start < duration_seconds:

                try:
                    raw = await asyncio.wait_for(
                        ws.recv(),
                        timeout=15,
                    )
                except asyncio.TimeoutError:
                    continue

                data = json.loads(raw)

                if data.get("error"):
                    print(
                        "[Deriv stream error]",
                        data["error"].get(
                            "message",
                            "Unknown error",
                        ),
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
                        "[Deriv callback error]",
                        callback_error,
                    )

    except Exception as exc:
        print(
            f"[Deriv stream error] {exc}"
        )


def deriv_connection_test(
    symbol: str = "XAUUSD",
) -> dict:

    price = get_deriv_price(symbol)

    if price is None:
        return {
            "connected": False,
            "symbol": symbol,
            "price": None,
            "message": "No Deriv tick received.",
        }

    return {
        "connected": True,
        "symbol": symbol,
        "price": price,
        "message": "Deriv tick received.",
    }


# ------------------------------------------------------------------
# Trading deliberately disabled in this version.
# ------------------------------------------------------------------

def execute_deriv_trade(*args, **kwargs) -> dict:
    return {
        "status": "disabled",
        "message": (
            "Live trade execution is intentionally disabled. "
            "Market-data connection must be verified first."
        ),
    }


__all__ = [
    "clean_symbol",
    "fetch_deriv_price_async",
    "get_deriv_price",
    "stream_ticks",
    "deriv_connection_test",
    "execute_deriv_trade",
]
