"""
SEKWAILA OMEGA X
Institutional Kill Zones
Version 3.0
"""

from datetime import datetime
from zoneinfo import ZoneInfo


class KillZones:

    def analyze(self):

        now = datetime.now(ZoneInfo("UTC"))
        london = now.astimezone(ZoneInfo("Europe/London"))
        newyork = now.astimezone(ZoneInfo("America/New_York"))

        london_hour = london.hour
        ny_hour = newyork.hour

        london_kz = 7 <= london_hour < 10
        ny_kz = 8 <= ny_hour < 11
        london_close = 15 <= london_hour < 17

        zone = "NONE"

        if london_kz:
            zone = "LONDON_OPEN"

        elif ny_kz:
            zone = "NEWYORK_OPEN"

        elif london_close:
            zone = "LONDON_CLOSE"

        confidence = 40

        if london_kz:
            confidence = 95

        elif ny_kz:
            confidence = 95

        elif london_close:
            confidence = 80

        return {

            "killzone": zone,

            "london_open": london_kz,

            "newyork_open": ny_kz,

            "london_close": london_close,

            "confidence": confidence

        }


killzones = KillZones()
