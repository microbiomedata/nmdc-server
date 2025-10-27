import re
from typing import Callable, Dict, List, Optional
from nmdc_server.config import settings
import nmdc_geoloc_tools

from nmdc_server.schemas_submission import MetadataSuggestionType


class SampleMetadataSuggester:
    """A class to suggest sample metadata values based on partial sample metadata."""

    @staticmethod
    def suggest_elevation_from_lat_lon(sample: Dict[str, str]) -> Optional[str]:
        """Suggest an elevation for a sample based on its lat_lon."""
        lat_lon = sample.get("lat_lon", None)
        if lat_lon is None:
            return None
        lat_lon_split = re.split("[, ]+", lat_lon)
        if len(lat_lon_split) == 2:
            try:
                lat, lon = map(float, lat_lon_split)

                elev = nmdc_geoloc_tools.elevation((lat, lon), settings.google_map_elevation_api_key)
                return f"{elev:.16g}"
            except ValueError:
                # This could happen if the lat_lon string is not parseable as a float
                # or nmdc_geoloc_tools determined they are invalid values. In either case,
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
        suggesters: dict[str, list[Callable[[dict[str, str]], Optional[str]]]] = {
            "elev": [self.suggest_elevation_from_lat_lon],
        }

        suggestions = {}

        for target_slot, suggester_list in suggesters.items():
            has_data = target_slot in sample and sample[target_slot]
            if (do_add and not has_data) or (do_replace and has_data):
                for suggester_fn in suggester_list:
                    suggestion = suggester_fn(sample)
                    if suggestion is not None and suggestion != sample.get(target_slot):
                        suggestions[target_slot] = suggestion

        return suggestions
