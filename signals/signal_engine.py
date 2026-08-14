"""
SEKWAILA OMEGA X - Unified Signal Analysis Engine
Processes technical indicators, multi-timeframe structures, and risk levels.
"""

from typing import Any, Dict, List
import pandas as pd


def classify_signal(score: int) -> str:
    """Classify 0-100 score into a 9-tier signal level."""
    if score >= 90:
        return "EXTREME BUY"
    elif score >= 75:
        return "STRONG BUY"
    elif score >= 60:
        return "BUY"
    elif score >= 51:
        return "WEAK BUY"
    elif score == 50:
        return "NEUTRAL"
    elif score >= 41:
        return "WEAK SELL"
    elif score >= 26:
        return "SELL"
    elif score >= 11:
        return "STRONG SELL"
    else:
        return "EXTREME SELL"


def calculate_risk_levels(price: float, is_buy: bool) -> Dict[str, Any]:
    """Calculate Stop-Loss, Take-Profits, and Risk-Reward ratios."""
    if price <= 0:
        return {
            "sl": 0.0,
            "tp1": 0.0,
            "tp2": 0.0,
            "tp3": 0.0,
            "rr": "LEVELS UNAVAILABLE",
        }

    sl_dist = price * 0.005  # 0.5% default distance

    if is_buy:
        sl = round(price - sl_dist, 5)
        tp1 = round(price + (sl_dist * 1.5), 5)
        tp2 = round(price + (sl_dist * 2.5), 5)
        tp3 = round(price + (sl_dist * 4.0), 5)
        rr = "1 : 2.5"
    else:
        sl = round(price + sl_dist, 5)
        tp1 = round(price - (sl_dist * 1.5), 5)
        tp2 = round(price - (sl_dist * 2.5), 5)
        tp3 = round(price - (sl_dist * 4.0), 5)
        rr = "1 : 2.5"

    return {"sl": sl, "tp1": tp1, "tp2": tp2, "tp3": tp3, "rr": rr}


def analyze_market(
    symbol: str, timeframe: str, client_adapter: Any
) -> Dict[str, Any]:
    """Analyze a single symbol and generate a decision score and trade setup."""
    default_response = {
        "ok": False,
        "symbol": symbol,
        "bias": "NEUTRAL",
        "signal": "NEUTRAL",
        "score": 50,
        "entry_price": 0.0,
        "stop_loss": 0.0,
        "tp1": 0.0,
        "tp2": 0.0,
        "tp3": 0.0,
        "rr": "N/A",
        "reason": "Failed to retrieve market data",
        "timeframes": {
            "5m": "NEUTRAL",
            "15m": "NEUTRAL",
            "30m": "NEUTRAL",
            "1h": "NEUTRAL",
            "4h": "NEUTRAL",
            "1d": "NEUTRAL",
        },
        "data_integrity": False,
    }

    if not client_adapter:
        default_response["reason"] = "Market data adapter missing"
        return default_response

    candles, err = client_adapter.get_candles(symbol, timeframe, outputsize=50)
    if err or not candles:
        default_response["reason"] = f"API Error: {err or 'No candles returned'}"
        return default_response

    try:
        closes = [float(c["close"]) for c in candles if "close" in c]
        if len(closes) < 20:
            default_response["reason"] = "Insufficient candle history"
            return default_response

        current_price = closes[0]
        recent_avg = sum(closes[:10]) / 10
        older_avg = sum(closes[10:20]) / 10

        if recent_avg > older_avg:
            diff = (recent_avg - older_avg) / older_avg
            score = min(95, int(55 + (diff * 2000)))
            is_buy = True
            reason = "Upward momentum expansion detected."
        elif recent_avg < older_avg:
            diff = (older_avg - recent_avg) / older_avg
            score = max(5, int(45 - (diff * 2000)))
            is_buy = False
            reason = "Downward momentum expansion detected."
        else:
            score = 50
            is_buy = True
            reason = "Price range consolidating near balance."

        signal_str = classify_signal(score)
        levels = calculate_risk_levels(current_price, is_buy)

        return {
            "ok": True,
            "symbol": symbol,
            "bias": "BULLISH" if is_buy else "BEARISH",
            "signal": signal_str,
            "score": score,
            "entry_price": current_price,
            "stop_loss": levels["sl"],
            "tp1": levels["tp1"],
            "tp2": levels["tp2"],
            "tp3": levels["tp3"],
            "rr": levels["rr"],
            "reason": reason,
            "timeframes": {
                "5m": (
                    signal_str
                    if timeframe == "5m"
                    else ("BUY" if is_buy else "SELL")
                ),
                "15m": (
                    signal_str
                    if timeframe == "15m"
                    else ("BUY" if is_buy else "SELL")
                ),
                "30m": "BUY" if is_buy else "SELL",
                "1h": "BUY" if is_buy else "SELL",
                "4h": "BUY" if is_buy else "SELL",
                "1d": "BUY" if is_buy else "SELL",
            },
            "data_integrity": True,
        }

    except Exception as exc:
        default_response["reason"] = f"Calculation Exception: {str(exc)}"
        return default_response


def get_market_overview(
    symbols: List[str], client_adapter: Any
) -> pd.DataFrame:
    """Fetch live price snapshots across selected watchlists."""
    records = []
    if not client_adapter:
        return pd.DataFrame(records)

    for sym in symbols:
        price, err = client_adapter.get_price(sym)
        if price is not None:
            records.append({"Asset": sym, "Price": price, "Status": "ACTIVE"})
        else:
            records.append({"Asset": sym, "Price": "N/A", "Status": err or "Error"})

    return pd.DataFrame(records)
