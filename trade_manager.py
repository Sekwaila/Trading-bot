"""
SEKWAILA OMEGA X
Trade Manager
"""

from database import db
from data.market_data import get_price
from logger import get_logger

logger = get_logger("trade_manager")


class TradeManager:

    def check_open_trades(self):

        trades = db.get_open_trades()

        if trades.empty:
            return

        for _, trade in trades.iterrows():

            price = get_price(trade["symbol"])

            if price is None:
                continue

            signal = trade["signal"]

            entry = float(trade["entry"])
            sl = float(trade["stop_loss"])
            tp = float(trade["tp1"])

            # BUY Trade
            if signal == "BUY":

                if price >= tp:

                    profit = round(tp - entry, 5)

                    db.update_trade(
                        trade["id"],
                        "WIN",
                        profit,
                    )

                    logger.info(
                        "%s BUY TP HIT",
                        trade["symbol"],
                    )

                elif price <= sl:

                    profit = round(sl - entry, 5)

                    db.update_trade(
                        trade["id"],
                        "LOSS",
                        profit,
                    )

                    logger.info(
                        "%s BUY SL HIT",
                        trade["symbol"],
                    )

            # SELL Trade
            else:

                if price <= tp:

                    profit = round(entry - tp, 5)

                    db.update_trade(
                        trade["id"],
                        "WIN",
                        profit,
                    )

                    logger.info(
                        "%s SELL TP HIT",
                        trade["symbol"],
                    )

                elif price >= sl:

                    profit = round(entry - sl, 5)

                    db.update_trade(
                        trade["id"],
                        "LOSS",
                        profit,
                    )

                    logger.info(
                        "%s SELL SL HIT",
                        trade["symbol"],
                    )


trade_manager = TradeManager()
