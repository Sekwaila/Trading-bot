from engine import generate_omega_signal
from config import ASSETS, DEFAULT_MIN_TF_AGREEMENT, DEFAULT_MIN_SCORE, DEFAULT_MIN_RR

asset, ticker = next(iter(ASSETS.items()))

result = generate_omega_signal(
    asset,
    ticker,
    DEFAULT_MIN_TF_AGREEMENT,
    DEFAULT_MIN_SCORE,
    DEFAULT_MIN_RR,
)

print("\n===== OMEGA ENGINE TEST =====")
print("Asset:", asset)
print("Ticker:", ticker)
print("OK:", result.get("ok"))

if result.get("ok"):
    print("Bias:", result["bias"])
    print("Score:", result["score"])
    print("Bull:", result["bull_score"])
    print("Bear:", result["bear_score"])
    print("Entry:", result["entry"])
    print("Stop:", result["stop"])
    print("TP1:", result["tp1"])
    print("TP2:", result["tp2"])
    print("TP3:", result["tp3"])
    print("RR:", result["rr"])
    print("Structure:", result["structure"])
    print("TF Biases:", result["tf_biases"])
else:
    print("Reason:", result.get("reason"))
    print("Integrity:", result.get("data_integrity"))
