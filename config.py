import os
from dataclasses import dataclass, field
from typing import List, Tuple
import datetime

@dataclass
class EngineConfig:
    SYMBOL: str = "GC=F"  # XAUUSD Gold Futures Proxy
    DISPLAY_SYMBOL: str = "XAUUSD"
    CONFLUENCE_THRESHOLD: float = 60.0
    RISK_PERCENT_DEFAULT: float = 1.0
    ACCOUNT_BALANCE_ZAR_DEFAULT: float = 10000.0
    CONTRACT_SIZE_OZ: float = 100.0  # 1 standard lot for XAUUSD = 100oz
    
    # Timeframe Mappings: (Period, Interval)
    TIMEFRAMES: dict = field(default_factory=lambda: {
        "1D": ("180d", "1d"),
        "4H": ("60d", "1h"),
        "1H": ("30d", "1h"),
        "15M": ("7d", "15m"),
    })
    
    # Static Placeholder News Windows (UTC)
    NEWS_BLACKOUT_WINDOWS_UTC: List[Tuple[datetime.time, datetime.time]] = field(
        default_factory=lambda: [
            (datetime.time(12, 20), datetime.time(12, 40)),
            (datetime.time(18, 0), datetime.time(18, 15)),
        ]
    )

config = EngineConfig()
