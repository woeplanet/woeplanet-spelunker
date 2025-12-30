"""
WOEplanet Spelunker: common package; coordinates extraction module.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class PlaceCoordinates:
    """
    Extracted centroid and bounding box from a place dict.
    """

    centroid: list[float] | None
    bounds: list[list[float]] | None


def extract_coordinates(place: dict[str, Any] | None) -> PlaceCoordinates:
    """
    Extract centroid and bounds from a place dictionary.
    """

    if not place:
        return PlaceCoordinates(centroid=None, bounds=None)

    centroid = None
    if place.get('lat') and place.get('lng'):
        centroid = [place['lat'], place['lng']]

    bounds = None
    if all(place.get(k) for k in ('sw_lat', 'sw_lng', 'ne_lat', 'ne_lng')):
        bounds = [
            [place['sw_lat'], place['sw_lng']],
            [place['ne_lat'], place['ne_lng']],
        ]

    return PlaceCoordinates(centroid=centroid, bounds=bounds)
