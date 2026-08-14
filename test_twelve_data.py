import os
import requests

# Load API key and allow lowercase 'import os' if run directly
API_KEY = os.getenv("TWELVE_DATA_API_KEY", "").strip()

if not API_KEY:
    print("ERROR: TWELVE_DATA_API_KEY is not available in environment.")
    raise SystemExit(1)

url = "https://api.twelvedata.com/time_series"

params = {
    "symbol": "XAU/USD",
    "interval": "15min",
    "outputsize": 5,
    "apikey": API_KEY,
}

try:
    response = requests.get(url, params=params, timeout=20)

    print("HTTP STATUS:", response.status_code)
    # Header check for API credits tracking (Handles response variations safely)
    credits_used = response.headers.get("api-credits-used") or response.headers.get("X-API-Credits-Used", "N/A")
    credits_left = response.headers.get("api-credits-left") or response.headers.get("X-API-Credits-Left", "N/A")
    
    print("API CREDITS USED:", credits_used)
    print("API CREDITS LEFT:", credits_left)

    data = response.json()

    # Check API level response status
    status = data.get("status")
    print("STATUS:", status)

    if status != "ok":
        print("MESSAGE:", data.get("message", "Unknown error"))
        print("CODE:", data.get("code", "N/A"))
        raise SystemExit(2)

    values = data.get("values", [])

    if not values:
        print("ERROR: XAU/USD returned no candle data.")
        raise SystemExit(3)

    print("\n✅ XAU/USD TEST SUCCESS")
    print("==================================================")

    for candle in values:
        print(
            f"DATETIME: {candle.get('datetime')} | "
            f"O: {candle.get('open')} | "
            f"H: {candle.get('high')} | "
            f"L: {candle.get('low')} | "
            f"C: {candle.get('close')}"
        )

except requests.RequestException as exc:
    print("REQUEST ERROR:", exc)
    raise SystemExit(4)
