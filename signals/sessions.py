"""
SEKWAILA OMEGA X
Institutional Trading Sessions
Version 3.0
"""

from datetime import datetime
from zoneinfo import ZoneInfo


class Sessions:

    def analyze(self):

        now = datetime.now(ZoneInfo("UTC"))

        london = now.astimezone(
            ZoneInfo("Europe/London")
        )

        newyork = now.astimezone(
            ZoneInfo("America/New_York")
        )

        london_open = 8 <= london.hour < 17
        newyork_open = 8 <= newyork.hour < 17

        overlap = london_open and newyork_open

        active = "ASIAN"

        if overlap:

            active = "LONDON_NEWYORK"

        elif london_open:

            active = "LONDON"

        elif newyork_open:

            active = "NEWYORK"

        confidence = 50

        if overlap:

            confidence = 100

        elif london_open or newyork_open:

            confidence = 90

        return {

            "session": active,

            "london": london_open,

            "newyork": newyork_open,

            "overlap": overlap,

            "confidence": confidence

        }


sessions = Sessions()
