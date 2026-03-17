import re
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

import nmdc_geoloc_tools

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

    @staticmethod
    def get_suggestions_from_study_information(
        submission: SubmissionMetadataSchema,
    ) -> List[MetadataSuggestion]:
        """Get suggestions based on study-level information from a submission"""

        # When run_recommendation_pipeline is available via `nmdc-metadata-suggestor-ai-tool`:
        # run_recommendation_pipeline(submission.model_dump())

        # For now, use a mock value:
        recommendation_pipeline_output = {
            "metadata_fields": [
                {
                    "field_name": "collection_date",
                    "reason": "Multiple sampling campaigns are reported (e.g., May, July, August 2016; June 2015/2016).",
                },
                {
                    "field_name": "collection_time",
                    "reason": "Sampling occurred on specific dates across seasons, making capture of time of sampling relevant.",
                },
                {
                    "field_name": "depth",
                    "reason": "Porewater and peat were sampled across 10–200 cm with specified intervals.",
                },
                {
                    "field_name": "elev",
                    "reason": "Field site context (Marcell Experimental Forest) requires elevation for location metadata.",
                },
                {
                    "field_name": "geo_loc_name",
                    "reason": "Sampling occurred at the S1 bog, Marcell Experimental Forest, Minnesota, USA.",
                },
                {
                    "field_name": "lat_lon",
                    "reason": "Coordinates are provided for the site (47°30.4760N; 93°27.1620W).",
                },
                {
                    "field_name": "growth_facil",
                    "reason": "Samples were collected in open-topped chamber enclosures as part of a whole-ecosystem warming field experiment.",
                },
                {
                    "field_name": "samp_store_temp",
                    "reason": "Samples (e.g., DNA and cores) were stored at −80 °C after collection.",
                },
                {
                    "field_name": "store_cond",
                    "reason": "Samples were frozen (e.g., shipped on dry ice and stored at −80 °C).",
                },
                {
                    "field_name": "samp_collec_device",
                    "reason": "A Russian corer and a serrated knife were used to collect peat; porewater collection methods are described.",
                },
                {
                    "field_name": "samp_collec_method",
                    "reason": "Methods detail peat coring, porewater collection, and headspace equilibration for gases.",
                },
                {
                    "field_name": "samp_size",
                    "reason": "Approximately 15 mL of peat per depth section was extracted for multi-omics analyses.",
                },
                {
                    "field_name": "temp",
                    "reason": "Peat temperature (e.g., measured at 50 cm) was recorded and used for regressions.",
                },
                {
                    "field_name": "air_temp_regm",
                    "reason": "Whole-ecosystem warming treatments increased air/peat temperatures by +2.25 to +9 °C.",
                },
                {
                    "field_name": "gaseous_environment",
                    "reason": "Chambers included manipulation of gaseous conditions (elevated CO2 atmosphere).",
                },
                {
                    "field_name": "chem_administration",
                    "reason": "Elevated air CO2 concentrations (~900 ppmv; +500 ppmv over ambient) were applied in some treatments.",
                },
                {
                    "field_name": "oxy_stat_samp",
                    "reason": "Study focuses on anaerobic/methanogenic conditions in peat porewater and peat profiles.",
                },
                {
                    "field_name": "env_broad_scale",
                    "reason": "Site is a forested bog in northern Minnesota consistent with a temperate coniferous forest biome context.",
                },
                {
                    "field_name": "env_local_scale",
                    "reason": "Local environment is a peatland/bog (S1 bog at Marcell Experimental Forest).",
                },
                {
                    "field_name": "env_medium",
                    "reason": "Samples are from peat soil (organic histosol) and porewater within the peat profile.",
                },
                {
                    "field_name": "ecosystem",
                    "reason": "Environmental study of a natural peatland system.",
                },
                {
                    "field_name": "ecosystem_category",
                    "reason": "The sampling environment is terrestrial.",
                },
                {
                    "field_name": "ecosystem_type",
                    "reason": "Samples are soils/peat from a terrestrial system.",
                },
                {
                    "field_name": "ecosystem_subtype",
                    "reason": "Peatland is a wetland subtype within terrestrial ecosystems.",
                },
                {
                    "field_name": "specific_ecosystem",
                    "reason": "The study targets peat within a bog system.",
                },
                {
                    "field_name": "analysis_type",
                    "reason": "Data types include metabolomics (GC-MS, NMR), lipidomics (LC-MS/MS), metaproteomics, metagenomics, amplicon sequencing (16S), natural organic matter (FTICR-MS of DOM), and bulk chemistry (CO2/CH4, isotopes).",
                },
                {
                    "field_name": "samp_name",
                    "reason": "Each peat/porewater sample and depth interval requires a unique local identifier.",
                },
                {
                    "field_name": "link_addit_analys",
                    "reason": "External repositories are cited (PRIDE PXD019912, NCBI BioProjects, JGI/SRA, SPRUCE repository DOI) for associated analyses.",
                },
                {
                    "field_name": "sample_link",
                    "reason": "Porewater and peat subsamples were split for multiple omics assays, requiring linkage between derived datasets.",
                },
            ],
            "model": "gpt-5-project",
            "access_provider": "pnnl",
        }
        suggestions: List[MetadataSuggestion] = []
        for metadata_field in recommendation_pipeline_output.get("metadata_fields", []):
            suggestions.append(
                MetadataSuggestion(
                    type=MetadataSuggestionType.ATTENTION,
                    slot=metadata_field["field_name"],  # type: ignore
                    source=metadata_field["reason"],  # type: ignore
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
