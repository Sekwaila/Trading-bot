import datetime
from typing import Tuple
from config import config

try:
    from zoneinfo import ZoneInfo
    _TZ_OK = True
except Exception:
    _TZ_OK = False

def check_session_validity() -> Tuple[bool, str]:
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    if _TZ_OK:
        try:
            london_hour = now_utc.astimezone(ZoneInfo("Europe/London")).hour
            ny_hour = now_utc.astimezone(ZoneInfo("America/New_York")).hour
            if (8 <= london_hour <= 16) or (8 <= ny_hour <= 17):
                return True, "ACTIVE_SESSION"
            return False, "REJECTED: Outside London/New York Session (DST-aware)"
        except Exception:
            pass

    if 6 <= now_utc.hour <= 20:
        return True, "ACTIVE_SESSION"
    return False, "REJECTED: Off-Peak Session (UTC fallback)"
