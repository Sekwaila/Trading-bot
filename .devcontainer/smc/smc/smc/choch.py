from typing import List, Dict


def detect_choch(
    candles: List[Dict],
    bos_events: List[Dict]
):
    """
    Detect Change of Character (CHoCH).

    A CHoCH occurs when the latest BOS is in the
    opposite direction of the previous BOS.
    """

    if len(bos_events) < 2:
        return []

    choch_events = []

    previous = bos_events[0]

    for current in bos_events[1:]:

        if previous["type"] != current["type"]:

            choch_events.append({

                "type": current["type"],

                "index": current["index"],

                "price": current["price"],

                "previous": previous["type"]

            })

        previous = current

    return choch_events
