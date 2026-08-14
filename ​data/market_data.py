"""
SEKWAILA OMEGA X
Unified market-data layer.

Normal markets:
    Twelve Data

Deriv synthetic markets:
    Deriv WebSocket
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from twelve_data_adapter import (
    get_live_price as twelve_live_price,
    get_candles as twelve_candles,
)

from deriv_adapter import (
    get_deriv_price,
    get_deriv_candles,
)


DERIV_SYMBOLS = {
    "VOL100",
    "VOL75",
    "VOL50",
    "BOOM1000",
    "CRASH1000",
    "BOOM500",
    "CRASH500",
}


def is_deriv_symbol(symbol: str) -> bool:
    return (
        str(symbol).upper().strip()
        in DERIV_SYMBOLS
    )


def get_live_price(
    symbol: str,
) -> Optional[float]:
    """Get latest price from correct provider."""

    clean = str(symbol).upper().strip()

    if is_deriv_symbol(clean):
        return get_deriv_price(clean)

    return twelve_live_price(clean)


def _interval_to_deriv_granularity(
    interval: str,
) -> int:

    mapping = {
        "1min": 60,
        "5min": 300,
        "15min": 900,
        "30min": 1800,
        "1h": 3600,
        "4h": 14400,
        "1day": 86400,
    }

    return mapping.get(
        str(interval).lower(),
        300,
    )


def get_candles(
    symbol: str,
    interval: str = "5min",
    limit: int = 100,
) -> pd.DataFrame:
    """Return normalized OHLC DataFrame."""

    clean = str(symbol).upper().strip()

    if is_deriv_symbol(clean):

        granularity = (
            _interval_to_deriv_granularity(
                interval
            )
        )

        candles = get_deriv_candles(
            clean,
            granularity=granularity,
            count=limit,
        )

    else:

        candles = twelve_candles(
            clean,
            interval=interval,
            outputsize=limit,
        )

    if not candles:
        return pd.DataFrame(
            columns=[
                "datetime",
                "open",
                "high",
                "low",
                "close",
                "volume",
            ]
        )

    df = pd.DataFrame(candles)

    required = [
        "open",
        "high",
        "low",
        "close",
    ]

    for column in required:
        if column not in df.columns:
            return pd.DataFrame()

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    if "volume" not in df.columns:
        df["volume"] = 0.0

    df["volume"] = pd.to_numeric(
        df["volume"],
        errors="coerce",
    ).fillna(0.0)

    df = df.dropna(
        subset=required
    ).reset_index(drop=True)

    return df


__all__ = [
    "get_live_price",
    "get_candles",
    "is_deriv_symbol",
]
