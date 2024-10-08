import re
from typing import Any, Callable, Dict, List, Optional

from nmdc_geoloc_tools import GeoEngine

from nmdc_server.schemas_submission import MetadataSuggestionType


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

    def suggest_elevation_from_lat_lon(self, sample: Dict[str, str]) -> Optional[float]:
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

    def get_suggestions(
        self, sample: Dict[str, str], *, types: Optional[List[MetadataSuggestionType]] = None
    ) -> Dict[str, str]:
        """Suggest metadata values for a sample.

        Returns a dictionary where the keys are sample metadata slots and the values are suggested
        values.
        """

        # Not explicitly supplying types implies using all types.
        if types is None:
            types = list(MetadataSuggestionType)

        do_add = MetadataSuggestionType.ADD in types
        do_replace = MetadataSuggestionType.REPLACE in types

        # Map from sample metadata slot to a list of functions that can suggest values for
        # that slot.
        suggesters: dict[str, list[Callable[[dict[str, str]], Optional[Any]]]] = {
            "elev": [self.suggest_elevation_from_lat_lon],
        }

        suggestions = {}

        for target_slot, suggester_list in suggesters.items():
            has_data = target_slot in sample and sample[target_slot]
            if (do_add and not has_data) or (do_replace and has_data):
                for suggester_fn in suggester_list:
                    suggestion = suggester_fn(sample)
                    if suggestion is not None:
                        suggestions[target_slot] = str(suggestion)

        return suggestions
