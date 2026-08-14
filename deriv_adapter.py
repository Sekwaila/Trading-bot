"""
SEKWAILA OMEGA X
Deriv market-data + trading adapter

- Discovers active Deriv symbols dynamically
- Gets single ticks
- Streams ticks
- Authenticates with DERIV_API_TOKEN for trading
- Uses current Deriv `underlying_symbol` parameter
"""

import os
import json
import asyncio
from typing import Optional, Dict, Any, Callable

import websockets

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


DERIV_APP_ID = os.getenv("DERIV_APP_ID", "1089").strip()
DERIV_API_TOKEN = os.getenv("DERIV_API_TOKEN", "").strip()

DERIV_WS_URL = (
    f"wss://ws.binaryws.com/websockets/v3"
    f"?app_id={DERIV_APP_ID}"
)


# User-facing symbol -> possible Deriv symbols.
# We do NOT blindly trust these. The adapter checks active_symbols.
SYMBOL_ALIASES = {
    "XAUUSD": [
        "frxXAUUSD",
        "XAUUSD",
    ],
    "EURUSD": [
        "frxEURUSD",
        "EURUSD",
    ],
    "GBPUSD": [
        "frxGBPUSD",
        "GBPUSD",
    ],
    "USDJPY": [
        "frxUSDJPY",
        "USDJPY",
    ],
    "AUDUSD": [
        "frxAUDUSD",
        "AUDUSD",
    ],
    "USDCAD": [
        "frxUSDCAD",
        "USDCAD",
    ],
    "USDCHF": [
        "frxUSDCHF",
        "USDCHF",
    ],
    "NZDUSD": [
        "frxNZDUSD",
        "NZDUSD",
    ],
    "BTCUSD": [
        "cryBTCUSD",
        "BTCUSD",
    ],
    "VOL10": ["R_10"],
    "VOL25": ["R_25"],
    "VOL50": ["R_50"],
    "VOL75": ["R_75"],
    "VOL100": ["R_100"],
    "BOOM1000": ["1HZ1000V"],
    "CRASH1000": ["1HZ1000S"],
}


def clean_symbol(symbol: str) -> str:
    """Normalise user input."""
    return (
        symbol
        .replace("/", "")
        .replace(" ", "")
        .upper()
        .strip()
    )


async def _request(ws, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Send JSON request and wait for matching response."""
    await ws.send(json.dumps(payload))

    while True:
        raw = await ws.recv()
        data = json.loads(raw)

        if "error" in data:
            return data

        return data


async def get_active_symbols_async() -> Dict[str, str]:
    """
    Retrieve Deriv active symbols.

    Returns:
        {
            "XAUUSD": "frxXAUUSD",
            "EURUSD": "frxEURUSD",
            ...
        }
    """

    try:
        async with websockets.connect(
            DERIV_WS_URL,
            open_timeout=10,
            close_timeout=5,
            ping_interval=20,
            ping_timeout=20,
        ) as ws:

            response = await _request(
                ws,
                {
                    "active_symbols": "full"
                }
            )

            if "error" in response:
                print(
                    "[Deriv active_symbols error]",
                    response["error"].get("message")
                )
                return {}

            symbols = response.get("active_symbols", [])

            result = {}

            for item in symbols:
                code = item.get("symbol")
                display = item.get("display_name", "")

                if not code:
                    continue

                code_upper = code.upper()
                display_upper = display.upper()

                # Store exact symbol codes using common aliases.
                for alias, candidates in SYMBOL_ALIASES.items():

                    if code in candidates:
                        result[alias] = code
                        continue

                    # Helpful fallback matching.
                    if alias == "XAUUSD" and (
                        "XAUUSD" in code_upper
                        or "GOLD" in display_upper
                    ):
                        result[alias] = code

                    elif alias == "EURUSD" and (
                        "EURUSD" in code_upper
                        or "EUR/USD" in display_upper
                    ):
                        result[alias] = code

                    elif alias == "GBPUSD" and (
                        "GBPUSD" in code_upper
                        or "GBP/USD" in display_upper
                    ):
                        result[alias] = code

                    elif alias == "BTCUSD" and (
                        "BTCUSD" in code_upper
                        or "BITCOIN" in display_upper
                    ):
                        result[alias] = code

            return result

    except Exception as exc:
        print("[Deriv active_symbols exception]", exc)
        return {}


async def resolve_symbol_async(symbol: str) -> Optional[str]:
    """Resolve a user symbol to a currently active Deriv symbol."""

    clean = clean_symbol(symbol)

    aliases = SYMBOL_ALIASES.get(clean, [])

    active = await get_active_symbols_async()

    # Prefer dynamically discovered symbol.
    if clean in active:
        return active[clean]

    # Exact candidate fallback.
    for candidate in aliases:
        if candidate in active.values():
            return candidate

    # If the user supplied a raw Deriv code, try it.
    if clean.startswith(("FRX", "R_", "1HZ", "CRY")):
        return clean

    return None


async def fetch_deriv_price_async(
    symbol: str
) -> Optional[float]:

    deriv_symbol = await resolve_symbol_async(symbol)

    if not deriv_symbol:
        print(
            f"[Deriv] No active symbol found for {symbol}"
        )
        return None

    try:
        async with websockets.connect(
            DERIV_WS_URL,
            open_timeout=10,
            close_timeout=5,
            ping_interval=20,
            ping_timeout=20,
        ) as ws:

            response = await _request(
                ws,
                {
                    "ticks": deriv_symbol,
                    "subscribe": 0,
                }
            )

            if "error" in response:
                print(
                    "[Deriv tick error]",
                    response["error"].get("message")
                )
                return None

            tick = response.get("tick", {})

            quote = tick.get("quote")

            if quote is None:
                print(
                    "[Deriv] Tick response contained no quote:",
                    response
                )
                return None

            return float(quote)

    except Exception as exc:
        print(
            f"[Deriv price exception] {symbol}: {exc}"
        )
        return None


def get_deriv_price(
    symbol: str
) -> Optional[float]:

    try:
        return asyncio.run(
            fetch_deriv_price_async(symbol)
        )
    except RuntimeError:
        return None
    except Exception as exc:
        print("[Deriv sync wrapper]", exc)
        return None


async def stream_ticks(
    symbol: str,
    callback: Callable[[float], None],
    duration_seconds: int = 60,
):
    """Subscribe to live Deriv ticks."""

    deriv_symbol = await resolve_symbol_async(symbol)

    if not deriv_symbol:
        print(
            f"[Deriv stream] Could not resolve {symbol}"
        )
        return

    try:
        async with websockets.connect(
            DERIV_WS_URL,
            open_timeout=10,
            close_timeout=5,
            ping_interval=20,
            ping_timeout=20,
        ) as ws:

            await ws.send(
                json.dumps(
                    {
                        "ticks": deriv_symbol,
                        "subscribe": 1,
                    }
                )
            )

            loop = asyncio.get_running_loop()
            start = loop.time()

            while loop.time() - start < duration_seconds:

                raw = await asyncio.wait_for(
                    ws.recv(),
                    timeout=20,
                )

                data = json.loads(raw)

                if "error" in data:
                    print(
                        "[Deriv stream error]",
                        data["error"].get("message")
                    )
                    break

                tick = data.get("tick")

                if not tick:
                    continue

                quote = tick.get("quote")

                if quote is None:
                    continue

                callback(float(quote))

    except Exception as exc:
        print(
            f"[Deriv stream exception] {symbol}: {exc}"
        )


async def execute_deriv_trade_async(
    symbol: str,
    direction: str,
    stake_amount: float = 10.0,
    multiplier: int = 10,
    currency: str = "USD",
) -> Dict[str, Any]:

    if not DERIV_API_TOKEN:
        return {
            "status": "error",
            "message": "DERIV_API_TOKEN is missing."
        }

    direction = direction.upper().strip()

    if direction not in {"BUY", "SELL"}:
        return {
            "status": "error",
            "message": "Direction must be BUY or SELL."
        }

    deriv_symbol = await resolve_symbol_async(symbol)

    if not deriv_symbol:
        return {
            "status": "error",
            "message": f"Could not resolve Deriv symbol for {symbol}."
        }

    contract_type = (
        "MULTUP"
        if direction == "BUY"
        else "MULTDOWN"
    )

    try:

        async with websockets.connect(
            DERIV_WS_URL,
            open_timeout=10,
            close_timeout=5,
            ping_interval=20,
            ping_timeout=20,
        ) as ws:

            # -----------------------------------------
            # 1. AUTHORIZE
            # -----------------------------------------

            auth_response = await _request(
                ws,
                {
                    "authorize": DERIV_API_TOKEN
                }
            )

            if "error" in auth_response:
                return {
                    "status": "error",
                    "message": auth_response["error"].get(
                        "message",
                        "Authorization failed."
                    )
                }

            # -----------------------------------------
            # 2. PROPOSAL
            # -----------------------------------------

            proposal_response = await _request(
                ws,
                {
                    "proposal": 1,
                    "amount": float(stake_amount),
                    "basis": "stake",
                    "contract_type": contract_type,
                    "currency": currency,
                    "multiplier": multiplier,
                    "underlying_symbol": deriv_symbol,
                }
            )

            if "error" in proposal_response:
                return {
                    "status": "error",
                    "message": proposal_response["error"].get(
                        "message",
                        "Proposal failed."
                    )
                }

            proposal = proposal_response.get(
                "proposal",
                {}
            )

            proposal_id = proposal.get("id")

            if not proposal_id:
                return {
                    "status": "error",
                    "message": "Deriv returned no proposal ID."
                }

            ask_price = float(
                proposal.get(
                    "ask_price",
                    stake_amount
                )
            )

            # -----------------------------------------
            # 3. BUY
            # -----------------------------------------

            buy_response = await _request(
                ws,
                {
                    "buy": proposal_id,
                    "price": ask_price,
                }
            )

            if "error" in buy_response:
                return {
                    "status": "error",
                    "message": buy_response["error"].get(
                        "message",
                        "Buy failed."
                    )
                }

            buy = buy_response.get(
                "buy",
                {}
            )

            return {
                "status": "success",
                "contract_id": buy.get("contract_id"),
                "purchase_price": buy.get(
                    "buy_price",
                    buy.get("purchase_price")
                ),
                "symbol": deriv_symbol,
                "direction": direction,
                "proposal_id": proposal_id,
            }

    except Exception as exc:

        return {
            "status": "error",
            "message": str(exc)
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

    except Exception as exc:

        return {
            "status": "error",
            "message": str(exc)
        }


__all__ = [
    "get_deriv_price",
    "stream_ticks",
    "execute_deriv_trade",
    "fetch_deriv_price_async",
    "execute_deriv_trade_async",
    "get_active_symbols_async",
    "resolve_symbol_async",
]
