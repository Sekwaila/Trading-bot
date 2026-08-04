"""
SEKWAILA OMEGA X V7
Premium / Discount Zones
"""


class PremiumDiscount:

    def analyze(self, df):

        if df is None or len(df) < 50:
            return None

        # Use recent swing range
        lookback = 50

        highest = df["high"].tail(lookback).max()
        lowest = df["low"].tail(lookback).min()

        current_price = float(df["close"].iloc[-2])

        equilibrium = (highest + lowest) / 2

        premium = False
        discount = False
        equilibrium_zone = False

        if current_price > equilibrium:
            premium = True

        elif current_price < equilibrium:
            discount = True

        else:
            equilibrium_zone = True

        return {

            "premium": premium,

            "discount": discount,

            "equilibrium": equilibrium_zone,

            "equilibrium_price": round(equilibrium, 5),

            "highest_price": round(float(highest), 5),

            "lowest_price": round(float(lowest), 5),

            "current_price": round(current_price, 5),

        }


premium_discount = PremiumDiscount()
