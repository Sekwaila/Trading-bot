"""
SEKWAILA OMEGA X — Signal Analysis Engine
"""

from typing import Any, Dict, List
import numpy as np
import pandas as pd


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def detect_smc_structures(df: pd.DataFrame) -> Dict[str, Any]:
    if len(df) < 15:
        return {
            "fvg_bullish": False,
            "fvg_bearish": False,
            "order_block": "NEUTRAL",
            "mss": "NONE",
        }

    close = df["close"].values
    high = df["high"].values
    low = df["low"].values

    fvg_bullish = low[-1] > high[-3]
    fvg_bearish = high[-1] < low[-3]

    recent_impulse = close[-1] - close[-5]
    if recent_impulse > 0 and low[-1] <= np.min(low[-10:-2]):
        order_block = "BULLISH_OB"
    elif recent_impulse < 0 and high[-1] >= np.max(high[-10:-2]):
        order_block = "BEARISH_OB"
    else:
        order_block = "NEUTRAL"

    prev_high = np.max(high[-15:-3])
    prev_low = np.min(low[-15:-3])

    if close[-1] > prev_high:
        mss = "BULLISH_BREAK"
    elif close[-1] < prev_low:
        mss = "BEARISH_BREAK"
    else:
        mss = "RANGE"

    return {
        "fvg_bullish": fvg_bullish,
        "fvg_bearish": fvg_bearish,
        "order_block": order_block,
        "mss": mss,
    }


def analyze_market(symbol: str, timeframe: str, client: Any) -> Dict[str, Any]:
    try:
        df = None
        if hasattr(client, "get_time_series"):
            df = client.get_time_series(
                symbol=symbol, interval=timeframe, outputsize=50
            )

        if df is None or df.empty or len(df) < 10:
            return {
                "ok": False,
                "reason": (
                    f"Unable to fetch data for {symbol}. "
                    "You may have exceeded Twelve Data's 8 req/min free rate limit, "
                    "or the API key is invalid."
                ),
            }

        df["rsi"] = calculate_rsi(df["close"], period=14)
        latest_rsi = (
            float(df["rsi"].iloc[-1]) if not np.isnan(df["rsi"].iloc[-1]) else 50.0
        )
        entry_price = float(df["close"].iloc[-1])

        smc = detect_smc_structures(df)

        tf_alignment = {
            "1m": "BULL" if latest_rsi > 50 else "BEAR",
            "5m": "BULL" if latest_rsi > 48 else "BEAR",
            "15m": "BULL" if latest_rsi > 52 else "BEAR",
            "1h": "BULL" if latest_rsi > 45 else "BEAR",
            "4h": "BULL" if latest_rsi > 50 else "BEAR",
            "1d": "BULL" if latest_rsi > 40 else "BEAR",
        }

        score = 50
        if smc["order_block"] == "BULLISH_OB":
            score += 15
        elif smc["order_block"] == "BEARISH_OB":
            score -= 15

        if smc["fvg_bullish"]:
            score += 12
        elif smc["fvg_bearish"]:
            score -= 12

        if smc["mss"] == "BULLISH_BREAK":
            score += 18
        elif smc["mss"] == "BEARISH_BREAK":
            score -= 18

        if latest_rsi > 60:
            score += 10
        elif latest_rsi < 40:
            score -= 10

        score = int(np.clip(score, 5, 98))

        if score >= 80:
            signal_label = "🔥 STRONG BUY"
            is_buy = True
        elif score >= 65:
            signal_label = "BUY"
            is_buy = True
        elif score >= 52:
            signal_label = "WEAK BUY"
            is_buy = True
        elif score <= 20:
            signal_label = "🔥 STRONG SELL"
            is_buy = False
        elif score <= 35:
            signal_label = "SELL"
            is_buy = False
        elif score <= 48:
            signal_label = "WEAK SELL"
            is_buy = False
        else:
            signal_label = "NEUTRAL"
            is_buy = True

        atr = entry_price * 0.004
        if is_buy:
            sl = round(entry_price - atr, 2)
            tp1 = round(entry_price + atr, 2)
            tp2 = round(entry_price + (atr * 2), 2)
        else:
            sl = round(entry_price + atr, 2)
            tp1 = round(entry_price - atr, 2)
            tp2 = round(entry_price - (atr * 2), 2)

        risk = abs(entry_price - sl)
        reward = abs(tp1 - entry_price)
        rr_ratio = f"1:{round(reward / risk, 2)}" if risk > 0 else "1:1.00"

        smc_desc = f"SMC: {smc['order_block']} | FVG: {'YES' if smc['fvg_bullish'] or smc['fvg_bearish'] else 'NO'} | RSI: {latest_rsi:.1f}"

        return {
            "ok": True,
            "symbol": symbol,
            "entry_price": f"{entry_price:.2f}",
            "signal": signal_label,
            "score": score,
            "stop_loss": f"{sl:.2f}",
            "tp1": f"{tp1:.2f}",
            "tp2": f"{tp2:.2f}",
            "rr": rr_ratio,
            "reason": smc_desc,
            "timeframes": tf_alignment,
        }

    except Exception as err:
        return {"ok": False, "reason": str(err)}


def get_market_overview(watchlist: List[str], client: Any) -> pd.DataFrame:
    results = []
    for item in watchlist:
        res = analyze_market(item, "15m", client)
        if res.get("ok"):
            results.append(
                {
                    "Asset": res["symbol"],
                    "Price": res["entry_price"],
                    "Signal": res["signal"],
                    "Confidence Score": f"{res['score']}%",
                    "R:R": res["rr"],
                    "Structure Notes": res["reason"],
                    "_score_raw": res["score"],
                }
            )

    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values(by="_score_raw", ascending=False).drop(
            columns=["_score_raw"]
        )

    return df
