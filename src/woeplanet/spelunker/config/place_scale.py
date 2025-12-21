"""
WOEplanet Spelunker: config package; place scale levels module.
"""

PLACETYPE_TO_SCALE: dict[int, int] = {
    19: 1,  # supername
    29: 2,  # continent
    38: 3,  # sea
    37: 3,  # ocean
    21: 4,  # region
    12: 5,  # country
    8: 6,  # state
    18: 7,  # nationality
    31: 8,  # timezone
    9: 9,  # county
    36: 10,  # aggregate
    13: 11,  # island
    16: 11,  # land feature
    24: 12,  # colloquial
    10: 13,  # local admin
    25: 14,  # zone
    15: 15,  # drainage
    7: 16,  # town
    22: 17,  # suburb
    33: 18,  # estate
    23: 19,  # sports team
    20: 19,  # poi
    14: 19,  # airport
    17: 20,  # miscellaneous
    6: 21,  # street
    32: 21,  # nearby intersection
    11: 22,  # zip
    26: 23,  # historical state
    27: 24,  # historical county
    35: 25,  # historical town
}


def placetype_to_scale(placetype_id: int) -> int:
    """
    Get the scale level for a placetype
    """

    return PLACETYPE_TO_SCALE.get(placetype_id, 0)
