from __future__ import annotations

from typing import Any, Dict, Optional

import requests


class GoogleMapsClient:
    def __init__(self, api_key: Optional[str]) -> None:
        self.api_key = api_key

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def reverse_geocode(self, latitude: Optional[float], longitude: Optional[float]) -> Optional[Dict[str, Any]]:
        if not self.enabled or latitude is None or longitude is None:
            return None

        response = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={
                "latlng": f"{latitude},{longitude}",
                "key": self.api_key,
            },
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()

        results = payload.get("results", [])
        if not results:
            return None

        top_result = results[0]
        return {
            "formatted_address": top_result.get("formatted_address"),
            "place_id": top_result.get("place_id"),
            "types": top_result.get("types", []),
        }


def build_google_maps_url(latitude: Optional[float], longitude: Optional[float]) -> Optional[str]:
    if latitude is None or longitude is None:
        return None
    return f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"
