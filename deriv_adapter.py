"""
SEKWAILA OMEGA X — DERIV WEBSOCKET ADAPTER

Provides 24/7 real-time tick streaming and direct trade execution for 
Synthetic Indices (Vol 75, Vol 100, Boom/Crash) and standard Forex/Metals.
"""

import os
import json
import asyncio
import websockets
from typing import Optional, Dict, Any, Callable

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

DERIV_APP_ID = os.getenv("DERIV_APP_ID", "1089")  # 1089 is default public App ID
DERIV_API_TOKEN = os.getenv("DERIV_API_TOKEN", "").strip()
DERIV_WS_URL = f"wss://ws.binaryws.com/websockets/v3?app_id={DERIV_APP_ID}"


# Symbol mapper to standardise asset inputs (e.g. XAUUSD -> frxXAUUSD, Vol100 -> R_100)
SYMBOL_MAP = {
    "XAUUSD": "frxXAUUSD",
    "EURUSD": "frxEURUSD",
    "GBPUSD": "frxGBPUSD",
    "BTCUSD": "cryBTCUSD",
    "VOL100": "R_100",
    "VOL75": "R_75",
    "VOL50": "R_50",
    "BOOM1000": "1HZ100V",
}


def _clean_symbol(symbol: str) -> str:
    """Translates user symbol input into Deriv API market ticker."""
    formatted = symbol.replace("/", "").upper().strip()
    return SYMBOL_MAP.get(formatted, formatted)


async def fetch_deriv_price_async(symbol: str) -> Optional[float]:
    """Asynchronously fetches the latest tick price for a given symbol."""
    deriv_symbol = _clean_symbol(symbol)
    request = {"ticks": deriv_symbol}

    try:
        async with websockets.connect(DERIV_WS_URL, timeout=8) as ws:
            await ws.send(json.dumps(request))
            response = await ws.recv()
            data = json.loads(response)

            if "tick" in data and "quote" in data["tick"]:
                return float(data["tick"]["quote"])
            elif "error" in data:
                print(f"[Deriv API Error] {data['error']['message']}")
    except Exception as exc:
        print(f"[Deriv Adapter Error] {exc}")

    return None


def get_deriv_price(symbol: str) -> Optional[float]:
    """Synchronous wrapper for engine compatibility."""
    try:
        return asyncio.run(fetch_deriv_price_async(symbol))
    except Exception:
        # Fallback if loop is already running in environment
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(fetch_deriv_price_async(symbol))


async def stream_ticks(symbol: str, callback: Callable[[float], None], duration_seconds: int = 60):
    """Subscribes to live Deriv ticks and executes a callback function per new price."""
    deriv_symbol = _clean_symbol(symbol)
    request = {"ticks": deriv_symbol, "subscribe": 1}

    try:
        async with websockets.connect(DERIV_WS_URL) as ws:
            await ws.send(json.dumps(request))
            start_time = asyncio.get_event_loop().time()

            while asyncio.get_event_loop().time() - start_time < duration_seconds:
                response = await ws.recv()
                data = json.loads(response)

                if "tick" in data and "quote" in data["tick"]:
                    quote = float(data["tick"]["quote"])
                    callback(quote)
    except Exception as exc:
        print(f"[Deriv Stream Listener Error] {exc}")


async def execute_deriv_trade_async(
    symbol: str,
    direction: str,  # "BUY" or "SELL"
    stake_amount: float = 10.0,
    multiplier: int = 10,
    currency: str = "USD"
) -> Dict[str, Any]:
    """Executes a live contract trade (Multipliers / CFDs) on Deriv API.

    Requires DERIV_API_TOKEN to be set in environment variables.
    """
    if not DERIV_API_TOKEN:
        return {"status": "error", "message": "DERIV_API_TOKEN is missing from environment."}

    deriv_symbol = _clean_symbol(symbol)
    contract_type = "MULTUP" if direction.upper() == "BUY" else "MULTDOWN"

    try:
        async with websockets.connect(DERIV_WS_URL) as ws:
            # 1. Authorize connection
            auth_req = {"authorize": DERIV_API_TOKEN}
            await ws.send(json.dumps(auth_req))
            auth_res = json.loads(await ws.recv())

            if "error" in auth_res:
                return {"status": "error", "message": auth_res["error"]["message"]}

            # 2. Get price proposal
            proposal_req = {
                "proposal": 1,
                "amount": stake_amount,
                "basis": "stake",
                "contract_type": contract_type,
                "currency": currency,
                "multiplier": multiplier,
                "symbol": deriv_symbol,
            }
            await ws.send(json.dumps(proposal_req))
            proposal_res = json.loads(await ws.recv())

            if "error" in proposal_res:
                return {"status": "error", "message": proposal_res["error"]["message"]}

            proposal_id = proposal_res["proposal"]["id"]

            # 3. Buy contract
            buy_req = {"buy": proposal_id, "price": stake_amount}
            await ws.send(json.dumps(buy_req))
            buy_res = json.loads(await ws.recv())

            if "error" in buy_res:
                return {"status": "error", "message": buy_res["error"]["message"]}

            contract_id = buy_res["buy"]["contract_id"]
            purchase_price = buy_res["buy"]["purchase_price"]

            return {
                "status": "success",
                "contract_id": contract_id,
                "purchase_price": purchase_price,
                "symbol": deriv_symbol,
                "direction": direction,
            }

    except Exception as exc:
        return {"status": "error", "message": str(exc)}


def execute_deriv_trade(symbol: str, direction: str, stake_amount: float = 10.0) -> Dict[str, Any]:
    """Synchronous execution helper for Streamlit buttons / auto-trader."""
    try:
        return asyncio.run(execute_deriv_trade_async(symbol, direction, stake_amount))
    except Exception:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(execute_deriv_trade_async(symbol, direction, stake_amount))


__all__ = [
    "get_deriv_price",
    "stream_ticks",
    "execute_deriv_trade",
    "fetch_deriv_price_async",
    "execute_deriv_trade_async",
]
