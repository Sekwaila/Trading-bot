"""
killzones.py – ICT Killzone Detection Module (SAST-aware)
Detects if the current time falls within major ICT killzones.
Supports timezone offset (e.g., +2 for South Africa).
"""

from datetime import datetime
import pandas as pd
from typing import Dict, Any, Optional

# Default killzone times in GMT
DEFAULT_KILLZONES = {
    "london": (7, 10),      # 07:00 – 10:00 GMT
    "new_york": (13, 16),   # 13:00 – 16:00 GMT
    "asia": (0, 4),         # 00:00 – 04:00 GMT
}

def analyze(df: pd.DataFrame, ctx: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Determines if the current time (from the last candle or now) is inside an ICT killzone.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with a DatetimeIndex. The last index is used as the current time.
    ctx : dict, optional
        Context dictionary passed by the engine. Can contain:
        - 'config': the engine's Config object (or a dict with 'killzone_times' and 'killzone_timezone_offset')
        - 'timezone_offset': integer hours to shift from GMT (e.g., 2 for SAST)

    Returns
    -------
    dict
        {
            "in_killzone": bool,
            "active_killzone": str or None,  # 'london', 'new_york', 'asia', or None
            "current_hour": int,
            "current_minute": int,
            "killzone_times": dict,          # the actual times used (after offset)
            "timezone_offset": int           # offset applied
        }
    """
    # Default values
    killzone_times = DEFAULT_KILLZONES.copy()
    timezone_offset = 0

    # Extract config if available
    if ctx:
        config = ctx.get('config')
        if config:
            # If config is a Config object or a dict
            if hasattr(config, 'get'):
                kz = config.get('killzone_times')
                if kz:
                    killzone_times.update(kz)
                tz = config.get('killzone_timezone_offset', 0)
                if tz:
                    timezone_offset = tz
            elif isinstance(config, dict):
                kz = config.get('killzone_times')
                if kz:
                    killzone_times.update(kz)
                tz = config.get('killzone_timezone_offset', 0)
                if tz:
                    timezone_offset = tz

        # Allow override via direct 'timezone_offset' key in ctx
        if 'timezone_offset' in ctx:
            timezone_offset = ctx['timezone_offset']

    # Determine current time
    if isinstance(df.index, pd.DatetimeIndex) and len(df) > 0:
        current_time = df.index[-1]
    else:
        current_time = datetime.now()

    # Apply timezone offset to convert to GMT
    # If your data is in SAST (UTC+2), set offset=2 to shift back to GMT
    current_time = current_time + pd.Timedelta(hours=-timezone_offset)
    current_hour = current_time.hour
    current_minute = current_time.minute

    # Check each killzone
    active_killzone = None
    in_killzone = False

    for name, (start_hour, end_hour) in killzone_times.items():
        # Handle windows that cross midnight (e.g., 22-02)
        if end_hour > start_hour:
            if start_hour <= current_hour < end_hour:
                in_killzone = True
                active_killzone = name
                break
        else:
            # Cross-midnight
            if current_hour >= start_hour or current_hour < end_hour:
                in_killzone = True
                active_killzone = name
                break

    return {
        "in_killzone": in_killzone,
        "active_killzone": active_killzone,
        "current_hour": current_hour,
        "current_minute": current_minute,
        "killzone_times": killzone_times,
        "timezone_offset": timezone_offset,
    }
