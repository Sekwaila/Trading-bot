import pandas as pd
from typing import Dict
from signals.market_structure import analyze_market_structure

def evaluate_mtf_bias(tf_data: Dict[str, pd.DataFrame]) -> Dict[str, str]:
    biases = {}
    for tf, df in tf_data.items():
        if df is not None:
            bias, _, _, _ = analyze_market_structure(df)
            biases[tf] = bias
        else:
            biases[tf] = "NEUTRAL"
    return biases
