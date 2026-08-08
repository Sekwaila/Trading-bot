import datetime as dt

def get_session_info():
    now = dt.datetime.now(dt.timezone.utc)
    hour = now.hour
    london = 8 <= hour <= 16
    ny = 13 <= hour <= 21
    
    if london and ny: return "LONDON / NY OVERLAP", "HIGH LIQUIDITY", 95
    if london: return "LONDON SESSION", "ACTIVE", 78
    if ny: return "NEW YORK SESSION", "ACTIVE", 82
    return "ASIA / OFF-PEAK", "LOWER LIQUIDITY", 48
