import re
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Dict, List, Optional

import nmdc_geoloc_tools
from nmdc_metadata_suggestor_ai_tool.llm_client import LLMClient
from nmdc_metadata_suggestor_ai_tool.recommendation_pipeline import run_recommendation_pipeline

from nmdc_server.config import settings
from nmdc_server.logger import get_logger
from nmdc_server.schemas_submission import (
    MetadataSuggestion,
    MetadataSuggestionType,
    SubmissionMetadataSchema,
)

logger = get_logger(__name__)


class Suggester(ABC):

    @property
    @abstractmethod
    def target_slots(self) -> List[str]:
        """The metadata slots that this suggester can provide suggestions for."""
        pass

    @abstractmethod
    def suggest(self, sample: Dict[str, str]) -> List[MetadataSuggestion]:
        """Returns a list of suggestions for the given sample."""
        pass


class ElevationSuggester(Suggester):

    def __init__(self):
        self.google_map_api_key = settings.google_map_api_key
        if not self.google_map_api_key:
            logger.warning(
                "Google Map API key is not set. ElevationSuggester cannot provide suggestions."
            )

    @property
    def target_slots(self) -> List[str]:
        return ["elev"]

    def suggest(self, sample: Dict[str, str]) -> List[MetadataSuggestion]:
        if not self.google_map_api_key:
            return []

        lat_lon = sample.get("lat_lon", None)
        if lat_lon is None:
            return []

        lat_lon_split = re.split("[, ]+", lat_lon)
        if len(lat_lon_split) == 2:
            try:
                lat, lon = map(float, lat_lon_split)

                elev = nmdc_geoloc_tools.elevation((lat, lon), settings.google_map_api_key)
                current_value = sample.get("elev")
                has_data = bool(current_value)
                return [
                    MetadataSuggestion(
                        slot="elev",
                        value=f"{elev:.2f}",
                        source="Google Maps API",
                        type=(
                            MetadataSuggestionType.REPLACE
                            if has_data
                            else MetadataSuggestionType.ADD
                        ),
                        is_ai_generated=False,
                        current_value=current_value,
                    )
                ]
            except ValueError:
                # This could happen if the lat_lon string is not parseable as a float
                # or nmdc_geoloc_tools determined they are invalid values. In either case,
                # just don't suggest an elevation.
                pass
        return []


class SampleMetadataSuggester:
    """A class to suggest sample metadata values based on partial sample metadata."""

    def get_suggestions_from_study_information(
        self,
        submission: SubmissionMetadataSchema,
    ) -> List[MetadataSuggestion]:
        """Get suggestions based on study-level information from a submission"""
        if not settings.llm_service_account_credentials_file:
            logger.warning(
                "LLM service account credentials file is not set. Not providing study-level suggestions."
            )
            return []

        llm_client = LLMClient(
            access_provider="gcp", credentials_file=settings.llm_service_account_credentials_file
        )
        recommendation_pipeline_output = run_recommendation_pipeline(
            submission.model_dump(),
            llm_client,
        )

        suggestions: List[MetadataSuggestion] = []
        for metadata_field in recommendation_pipeline_output.metadata_fields:
            suggestions.append(
                MetadataSuggestion(
                    type=MetadataSuggestionType.ATTENTION,
                    slot=metadata_field.field_name,
                    source=metadata_field.reason,
                    is_ai_generated=True,
                )
            )
        return suggestions

    def get_suggestions(
        self, sample: Dict[str, str], *, types: Optional[List[MetadataSuggestionType]] = None
    ) -> List[MetadataSuggestion]:
        """Suggest metadata values for a sample."""

        # Not explicitly supplying types implies using all types.
        if types is None:
            types = list(MetadataSuggestionType)

        do_add = MetadataSuggestionType.ADD in types
        do_replace = MetadataSuggestionType.REPLACE in types

        # List of suggester functions to apply, in order. Each suggester function is associated
        # with a target metadata slot that it provides suggestions for.
        suggesters: list[Suggester] = [
            ElevationSuggester(),
        ]

        suggestions = []

        for suggester in suggesters:
            # Preflight: Run the suggester if ANY of its target slots are candidates for suggestion
            # based on the presence/absence of values in the sample row and the types of suggestions
            # requested.
            is_eligible = any(
                (
                    do_add and not sample.get(slot) or (do_replace and sample.get(slot))
                    for slot in suggester.target_slots
                )
            )

            if not is_eligible:
                continue

            new_suggestions = suggester.suggest(sample)
            for suggestion in new_suggestions:
                if suggestion.type in types and suggestion.value != sample.get(suggestion.slot):
                    suggestions.append(suggestion)

        return suggestions


@lru_cache(maxsize=1)
def get_sample_metadata_suggester() -> SampleMetadataSuggester:
    """Get a cached instance of SampleMetadataSuggester."""
    return SampleMetadataSuggester()
