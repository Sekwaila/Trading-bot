"""
SEKWAILA OMEGA X
Institutional Premium / Discount Engine
Version 3.0
"""


class PremiumDiscount:

    def analyze(self, df, structure):

        if df is None:
            return None

        if structure is None:
            return None

        if len(df) < 30:
            return None

        swing_high = structure["last_high"]
        swing_low = structure["last_low"]

        if swing_high is None or swing_low is None:
            return None

        current_price = float(df["close"].iloc[-2])

        equilibrium = (swing_high + swing_low) / 2

        zone = "EQUILIBRIUM"

        if current_price > equilibrium:
            zone = "PREMIUM"

        elif current_price < equilibrium:
            zone = "DISCOUNT"

        distance = abs(current_price - equilibrium)

        range_size = swing_high - swing_low

        if range_size == 0:
            confidence = 50
        else:
            confidence = min(
                100,
                round((distance / range_size) * 200)
            )

        return {

            "zone": zone,

            "premium": zone == "PREMIUM",

            "discount": zone == "DISCOUNT",

            "equilibrium": equilibrium,

            "current_price": current_price,

            "confidence": confidence

        }


premium_discount = PremiumDiscount()
