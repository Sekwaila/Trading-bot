import datetime

def get_current_killzone() -> str:
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    hour = now_utc.hour
    if 7 <= hour <= 10:
        return "LONDON_OPEN_KILLZONE"
    elif 13 <= hour <= 16:
        return "NEW_YORK_OPEN_KILLZONE"
    elif 16 <= hour <= 18:
        return "LONDON_CLOSE_KILLZONE"
    elif 0 <= hour <= 4:
        return "ASIAN_KILLZONE"
    return "OUTSIDE_KILLZONE"
