import re
from typing import Dict, Optional

from nmdc_geoloc_tools import GeoEngine


class SampleMetadataSuggester:
    """A class to suggest sample metadata values based on partial sample metadata."""

    def __init__(self):
        self._geo_engine: Optional[GeoEngine] = None

    @property
    def geo_engine(self) -> GeoEngine:
        """A GeoEngine instance for looking up geospatial data."""
        if self._geo_engine is None:
            self._geo_engine = GeoEngine()
        return self._geo_engine

    def suggest_elevation(self, sample: Dict[str, str]) -> Optional[float]:
        """Suggest an elevation for a sample based on its lat_lon."""
        lat_lon = sample.get("lat_lon", None)
        if lat_lon is None:
            return None
        lat_lon_split = re.split("[, ]+", lat_lon)
        if len(lat_lon_split) == 2:
            try:
                lat, lon = map(float, lat_lon_split)
                return self.geo_engine.get_elevation((lat, lon))
            except ValueError:
                # This could happen if the lat_lon string is not parseable as a float
                # or the GeoEngine determined they are invalid values. In either case,
                # just don't suggest an elevation.
                pass
        return None

    def get_suggestions(self, sample: Dict[str, str]) -> Dict[str, str]:
        """Suggest metadata values for a sample.

        Returns a dictionary where the keys are sample metadata slots and the values are suggested
        values.
        """
        suggestions = {}
        elevation = self.suggest_elevation(sample)
        if elevation is not None:
            suggestions["elev"] = str(elevation)
        return suggestions
