import logging

logger = logging.getLogger(__name__)

class TradeManager:
    """
    Safe trade manager configured strictly to log signals.
    Execution is completely disabled.
    """
    def __init__(self):
        self.auto_trade_enabled = False

    def process_signal(self, symbol: str, signal_type: str, price: float):
        logger.info(f"[Signal Engine Log] Symbol: {symbol} | Type: {signal_type} | Price: {price}")
        print(f"📡 SIGNAL LOGGED: {signal_type} for {symbol} at {price:.2f}")
