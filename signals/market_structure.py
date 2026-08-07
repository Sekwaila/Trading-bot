"""
===============================================================================
SEKWAILA OMEGA X
Institutional Market Structure Engine
Version 9.0

Detects:
- Swing Highs
- Swing Lows
- External Structure
- Internal Structure
- BOS
- CHoCH
- MSS
- Liquidity Sweeps
- Trend Bias
===============================================================================
"""

from dataclasses import dataclass
from typing import List, Optional

import numpy as np
import pandas as pd


@dataclass
class SwingPoint:
    index: int
    price: float
    kind: str


class MarketStructure:

    def __init__(self, swing_length: int = 5):

        self.swing_length = swing_length

    def _validate_dataframe(self, df: pd.DataFrame):

        required = ["open", "high", "low", "close"]

        for column in required:

            if column not in df.columns:
                raise ValueError(f"Missing column: {column}")

        if len(df) < (self.swing_length * 4):
            return False

        return True
