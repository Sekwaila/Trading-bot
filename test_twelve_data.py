import os
import requests

API_KEY = os.getenv("TWELVE_DATA_API_KEY", "").strip()

if not API_KEY:
    print("ERROR: TWELVE_DATA_API_KEY is not available.")
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
    print("API CREDITS USED:", response.headers.get("api-credits-used"))
    print("API CREDITS LEFT:", response.headers.get("api-credits-left"))

    data = response.json()

    print("STATUS:", data.get("status"))

    if data.get("status") != "ok":
        print("MESSAGE:", data.get("message"))
        print("CODE:", data.get("code"))
        raise SystemExit(2)

    values = data.get("values", [])

    if not values:
        print("ERROR: XAU/USD returned no candles.")
        raise SystemExit(3)

    print("\nXAU/USD TEST SUCCESS")
    print("====================")

    for candle in values:
        print(
            candle.get("datetime"),
            "OPEN=", candle.get("open"),
            "HIGH=", candle.get("high"),
            "LOW=", candle.get("low"),
            "CLOSE=", candle.get("close"),
        )

except requests.RequestException as exc:
    print("REQUEST ERROR:", exc)
    raise SystemExit(4)
