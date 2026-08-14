"""
SEKWAILA OMEGA X
Deriv WebSocket adapter.

Market data:
    - public WebSocket
    - no authentication required

Trading:
    - authentication token required
    - disabled by default
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from typing import Optional, Dict, Any, Callable

import websockets


PUBLIC_WS_URL = "wss://ws.binaryws.com/websockets/v3"


def _get_secret(name: str, default: str = "") -> str:
    """Read a secret from Streamlit Secrets, then environment."""

    try:
        import streamlit as st

        value = st.secrets.get(name, "")

        if value:
            return str(value).strip()

    except Exception:
        pass

    return os.getenv(name, default).strip()


DERIV_API_TOKEN = _get_secret("DERIV_API_TOKEN")
DERIV_APP_ID = _get_secret("DERIV_APP_ID", "1089")


# Friendly application names -> possible Deriv symbols.
SYMBOL_CANDIDATES = {
    "VOL100": [
        "1HZ100V",
        "R_100",
    ],
    "VOL75": [
        "R_75",
        "1HZ75V",
    ],
    "VOL50": [
        "R_50",
        "1HZ50V",
    ],
    "BOOM1000": [
        "BOOM1000",
    ],
    "CRASH1000": [
        "CRASH1000",
    ],
    "BOOM500": [
        "BOOM500",
    ],
    "CRASH500": [
        "CRASH500",
    ],
    "EURUSD": [
        "frxEURUSD",
    ],
    "GBPUSD": [
        "frxGBPUSD",
    ],
    "USDJPY": [
        "frxUSDJPY",
    ],
    "AUDUSD": [
        "frxAUDUSD",
    ],
    "USDCAD": [
        "frxUSDCAD",
    ],
    "USDCHF": [
        "frxUSDCHF",
    ],
    "NZDUSD": [
        "frxNZDUSD",
    ],
    "XAUUSD": [
        "frxXAUUSD",
    ],
    "BTCUSD": [
        "cryBTCUSD",
    ],
}


def _clean_symbol(symbol: str) -> str:
    if not symbol:
        return ""

    return (
        str(symbol)
        .replace("/", "")
        .replace(" ", "")
        .replace("-", "")
        .upper()
        .strip()
    )


async def _connect():
    """
    Connect using the public Deriv WebSocket.

    websockets 16 uses open_timeout rather than the old timeout
    argument used by older examples.
    """

    return await websockets.connect(
        PUBLIC_WS_URL,
        open_timeout=10,
        close_timeout=3,
        ping_interval=20,
        ping_timeout=20,
        max_size=2_000_000,
    )


async def _request(
    payload: Dict[str, Any],
    timeout: float = 10,
) -> Optional[Dict[str, Any]]:
    """Send one request and wait for the matching useful response."""

    try:
        async with await _connect() as ws:

            await ws.send(json.dumps(payload))

            end_time = time.monotonic() + timeout

            while time.monotonic() < end_time:

                remaining = max(
                    0.1,
                    end_time - time.monotonic(),
                )

                try:
                    raw = await asyncio.wait_for(
                        ws.recv(),
                        timeout=remaining,
                    )
                except asyncio.TimeoutError:
                    break

                data = json.loads(raw)

                if "error" in data:
                    print(
                        "[Deriv API Error]",
                        data["error"].get("message", "Unknown error"),
                    )
                    return data

                return data

    except Exception as exc:
        print(f"[Deriv WebSocket Error] {exc}")

    return None


async def get_active_symbols_async() -> list[dict]:
    """Retrieve currently active Deriv symbols."""

    data = await _request(
        {
            "active_symbols": "brief",
            "product_type": "basic",
            "req_id": 1,
        }
    )

    if not data:
        return []

    symbols = data.get("active_symbols", [])

    if not isinstance(symbols, list):
        return []

    return symbols


def get_active_symbols() -> list[dict]:
    try:
        return asyncio.run(get_active_symbols_async())
    except RuntimeError:
        return []


async def resolve_deriv_symbol_async(symbol: str) -> Optional[str]:
    """
    Resolve a friendly symbol into an actually active Deriv symbol.

    This avoids relying completely on hard-coded symbol names.
    """

    clean = _clean_symbol(symbol)

    candidates = SYMBOL_CANDIDATES.get(
        clean,
        [clean],
    )

    active = await get_active_symbols_async()

    active_codes = {
        str(item.get("symbol", "")).upper()
        for item in active
        if item.get("symbol")
    }

    # First try explicit candidates.
    for candidate in candidates:
        if candidate.upper() in active_codes:
            return candidate

    # Try matching the display name.
    search_words = {
        "VOL100": ["VOLATILITY 100"],
        "VOL75": ["VOLATILITY 75"],
        "VOL50": ["VOLATILITY 50"],
        "BOOM1000": ["BOOM 1000"],
        "CRASH1000": ["CRASH 1000"],
    }

    for item in active:
        code = str(item.get("symbol", ""))
        display = str(
            item.get("display_name", "")
        ).upper()

        for word in search_words.get(clean, []):
            if word in display:
                return code

    # If we don't have active-symbol data, use the first candidate.
    if candidates:
        return candidates[0]

    return None


def resolve_deriv_symbol(symbol: str) -> Optional[str]:
    try:
        return asyncio.run(
            resolve_deriv_symbol_async(symbol)
        )
    except RuntimeError:
        return None


async def fetch_deriv_price_async(
    symbol: str,
) -> Optional[float]:
    """Fetch one current Deriv tick."""

    deriv_symbol = await resolve_deriv_symbol_async(symbol)

    if not deriv_symbol:
        return None

    data = await _request(
        {
            "ticks": deriv_symbol,
            "subscribe": 0,
            "req_id": 10,
        },
        timeout=10,
    )

    if not data:
        return None

    if "error" in data:
        return None

    tick = data.get("tick", {})

    try:
        return float(tick["quote"])
    except (KeyError, TypeError, ValueError):
        return None


def get_deriv_price(
    symbol: str,
) -> Optional[float]:
    """Synchronous price helper."""

    try:
        return asyncio.run(
            fetch_deriv_price_async(symbol)
        )
    except RuntimeError:
        return None


async def get_deriv_candles_async(
    symbol: str,
    granularity: int = 300,
    count: int = 100,
) -> list[dict]:
    """Retrieve historical Deriv OHLC candles."""

    deriv_symbol = await resolve_deriv_symbol_async(symbol)

    if not deriv_symbol:
        return []

    data = await _request(
        {
            "ticks_history": deriv_symbol,
            "end": "latest",
            "style": "candles",
            "granularity": int(granularity),
            "count": max(10, min(int(count), 5000)),
            "subscribe": 0,
            "req_id": 20,
        },
        timeout=15,
    )

    if not data:
        return []

    raw_candles = data.get("candles", [])

    if not isinstance(raw_candles, list):
        return []

    candles = []

    for candle in raw_candles:
        try:
            candles.append(
                {
                    "datetime": candle.get("epoch"),
                    "open": float(candle["open"]),
                    "high": float(candle["high"]),
                    "low": float(candle["low"]),
                    "close": float(candle["close"]),
                    "volume": 0.0,
                }
            )
        except (KeyError, TypeError, ValueError):
            continue

    return candles


def get_deriv_candles(
    symbol: str,
    granularity: int = 300,
    count: int = 100,
) -> list[dict]:
    """Synchronous candle helper."""

    try:
        return asyncio.run(
            get_deriv_candles_async(
                symbol,
                granularity,
                count,
            )
        )
    except RuntimeError:
        return []


async def stream_ticks(
    symbol: str,
    callback: Callable[[float], None],
    duration_seconds: int = 60,
):
    """Subscribe to a Deriv tick stream."""

    deriv_symbol = await resolve_deriv_symbol_async(symbol)

    if not deriv_symbol:
        return

    try:

        async with await _connect() as ws:

            await ws.send(
                json.dumps(
                    {
                        "ticks": deriv_symbol,
                        "subscribe": 1,
                        "req_id": 30,
                    }
                )
            )

            end_time = time.monotonic() + duration_seconds

            while time.monotonic() < end_time:

                try:
                    raw = await asyncio.wait_for(
                        ws.recv(),
                        timeout=10,
                    )
                except asyncio.TimeoutError:
                    continue

                data = json.loads(raw)

                if "error" in data:
                    print(
                        "[Deriv Stream Error]",
                        data["error"].get("message"),
                    )
                    break

                tick = data.get("tick")

                if not tick:
                    continue

                try:
                    quote = float(tick["quote"])
                    callback(quote)
                except (KeyError, TypeError, ValueError):
                    continue

    except Exception as exc:
        print(
            f"[Deriv Stream Listener Error] {exc}"
        )


async def execute_deriv_trade_async(
    symbol: str,
    direction: str,
    stake_amount: float = 10.0,
    multiplier: int = 10,
    currency: str = "USD",
) -> Dict[str, Any]:
    """
    Legacy Deriv contract execution helper.

    IMPORTANT:
    The application should keep live execution disabled by default.

    This function only executes when DERIV_LIVE_TRADING_ENABLED=true.
    """

    live_enabled = _get_secret(
        "DERIV_LIVE_TRADING_ENABLED",
        "false",
    ).lower() == "true"

    if not live_enabled:
        return {
            "status": "disabled",
            "message": (
                "Live Deriv execution is disabled. "
                "Set DERIV_LIVE_TRADING_ENABLED=true "
                "only after testing on demo."
            ),
        }

    if not DERIV_API_TOKEN:
        return {
            "status": "error",
            "message": "DERIV_API_TOKEN is missing.",
        }

    deriv_symbol = await resolve_deriv_symbol_async(symbol)

    if not deriv_symbol:
        return {
            "status": "error",
            "message": "Could not resolve Deriv symbol.",
        }

    direction = direction.upper().strip()

    if direction not in {"BUY", "SELL"}:
        return {
            "status": "error",
            "message": "Direction must be BUY or SELL.",
        }

    contract_type = (
        "MULTUP"
        if direction == "BUY"
        else "MULTDOWN"
    )

    try:

        async with await _connect() as ws:

            # Authorize.
            await ws.send(
                json.dumps(
                    {
                        "authorize": DERIV_API_TOKEN,
                        "req_id": 100,
                    }
                )
            )

            auth = json.loads(
                await ws.recv()
            )

            if "error" in auth:
                return {
                    "status": "error",
                    "message": auth["error"].get(
                        "message",
                        "Authorization failed",
                    ),
                }

            # Proposal.
            await ws.send(
                json.dumps(
                    {
                        "proposal": 1,
                        "amount": float(stake_amount),
                        "basis": "stake",
                        "contract_type": contract_type,
                        "currency": currency,
                        "multiplier": int(multiplier),
                        "underlying_symbol": deriv_symbol,
                        "req_id": 101,
                    }
                )
            )

            proposal = json.loads(
                await ws.recv()
            )

            if "error" in proposal:
                return {
                    "status": "error",
                    "message": proposal["error"].get(
                        "message",
                        "Proposal failed",
                    ),
                }

            proposal_obj = proposal.get(
                "proposal",
                {},
            )

            proposal_id = proposal_obj.get("id")

            if not proposal_id:
                return {
                    "status": "error",
                    "message": "No proposal ID returned.",
                }

            # Buy.
            await ws.send(
                json.dumps(
                    {
                        "buy": proposal_id,
                        "price": float(stake_amount),
                        "req_id": 102,
                    }
                )
            )

            buy = json.loads(
                await ws.recv()
            )

            if "error" in buy:
                return {
                    "status": "error",
                    "message": buy["error"].get(
                        "message",
                        "Buy failed",
                    ),
                }

            result = buy.get("buy", {})

            return {
                "status": "success",
                "contract_id": result.get(
                    "contract_id"
                ),
                "purchase_price": result.get(
                    "purchase_price"
                ),
                "symbol": deriv_symbol,
                "direction": direction,
            }

    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
        }


def execute_deriv_trade(
    symbol: str,
    direction: str,
    stake_amount: float = 10.0,
) -> Dict[str, Any]:

    try:
        return asyncio.run(
            execute_deriv_trade_async(
                symbol,
                direction,
                stake_amount,
            )
        )
    except RuntimeError:
        return {
            "status": "error",
            "message": (
                "Could not start Deriv execution loop."
            ),
        }


__all__ = [
    "get_deriv_price",
    "get_deriv_candles",
    "get_active_symbols",
    "resolve_deriv_symbol",
    "stream_ticks",
    "execute_deriv_trade",
    "fetch_deriv_price_async",
    "execute_deriv_trade_async",
]
