import datetime as dt

def is_in_killzone() -> tuple[bool, str]:
    now = dt.datetime.now(dt.timezone.utc)
    hour = now.hour
    if 7 <= hour <= 10: return True, "LONDON KILLZONE"
    if 12 <= hour <= 15: return True, "NY KILLZONE"
    if 0 <= hour <= 3: return True, "ASIAN KILLZONE"
    return False, "OUTSIDE KILLZONE"
