"""
SEKWAILA OMEGA X
Sessions
"""

import pandas as pd


class Sessions:

    def analyze(self, df):

        if df is None or len(df) == 0:
            return None

        # Use last CLOSED candle
        last = df.iloc[-2]

        ts = pd.to_datetime(last["time"])

        hour = ts.hour

        asian = 0 <= hour < 8
        london = 8 <= hour < 16
        new_york = 13 <= hour < 21

        active_session = "None"

        if london:
            active_session = "London"
        elif new_york:
            active_session = "New York"
        elif asian:
            active_session = "Asian"

        return {

            "asian": asian,
            "london": london,
            "new_york": new_york,
            "active_session": active_session,

        }


sessions = Sessions()
