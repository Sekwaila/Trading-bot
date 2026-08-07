from typing import Optional, Dict

def calculate_position_size(account_balance_usd: Optional[float], risk_pct: float,
                            entry_price: float, stop_loss_price: float,
                            contract_size_oz: float = 100.0) -> Optional[Dict]:
    if not account_balance_usd or account_balance_usd <= 0:
        return None
    stop_distance = abs(entry_price - stop_loss_price)
    if stop_distance <= 0:
        return None

    risk_amount_usd = account_balance_usd * (risk_pct / 100.0)
    lots = risk_amount_usd / (stop_distance * contract_size_oz)

    return {
        "risk_amount_usd": round(risk_amount_usd, 2),
        "stop_distance": round(stop_distance, 2),
        "lots": round(lots, 3),
    }
