"""
SEKWAILA OMEGA X — RISK & SIZING CALCULATOR
============================================
Signal-Only Architecture. Calculates position metrics.
"""
from typing import Dict, Any, Optional

def calculate_position_size(
    account_zar: float,
    risk_pct: float,
    usd_zar: Optional[float],
    entry: float,
    stop: float
) -> Dict[str, Any]:
    risk_zar = account_zar * (risk_pct / 100.0)
    if not usd_zar or usd_zar <= 0:
        return {"risk_zar": risk_zar, "risk_usd": None, "lots": None}
    
    risk_usd = risk_zar / usd_zar
    stop_dist = abs(entry - stop)
    if stop_dist == 0:
        return {"risk_zar": risk_zar, "risk_usd": risk_usd, "lots": 0.0}
        
    lots = risk_usd / (stop_dist * 100)
    return {
        "risk_zar": round(risk_zar, 2),
        "risk_usd": round(risk_usd, 2),
        "lots": round(lots, 3)
    }
