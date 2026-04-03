from __future__ import annotations

from functools import lru_cache

from config import Config

try:
    import googlemaps
except ImportError:  # pragma: no cover
    googlemaps = None


@lru_cache(maxsize=256)
def get_address(lat: float, lng: float) -> str:
    """
    Reverse geocode coordinates to street address using Google Maps API.
    Cache results to avoid duplicate API calls.
    Return 'Unknown Location' if API call fails.
    """
    try:
        if googlemaps is None:
            return "Unknown Location"
        client = googlemaps.Client(key=Config.GOOGLE_MAPS_API_KEY)
        results = client.reverse_geocode((lat, lng))
        if not results:
            return "Unknown Location"
        return results[0].get("formatted_address", "Unknown Location")
    except Exception as exc:
        print(f"[MAPS][WARN] Reverse geocoding failed: {exc}")
        return "Unknown Location"


def get_maps_link(lat: float, lng: float) -> str:
    """Return a clickable Google Maps URL for the coordinates."""
    return f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"


def detect_zone(address: str) -> str:
    """
    Try to detect zone name from address string.
    Return 'Unknown Zone' if not detectable.
    """
    try:
        if not address or address == "Unknown Location":
            return "Unknown Zone"
        parts = [part.strip() for part in address.split(",") if part.strip()]
        if len(parts) >= 3:
            return parts[-3]
        if parts:
            return parts[0]
        return "Unknown Zone"
    except Exception as exc:
        print(f"[MAPS][WARN] Zone detection failed: {exc}")
        return "Unknown Zone"

