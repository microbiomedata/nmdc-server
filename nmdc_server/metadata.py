import re
from typing import Callable, Dict, List, Optional

import nmdc_geoloc_tools

from nmdc_server.config import settings
from nmdc_server.logger import get_logger
from nmdc_server.schemas_submission import MetadataSuggestionType, SubmissionMetadataSchema


class SampleMetadataSuggester:
    """A class to suggest sample metadata values based on partial sample metadata."""

    @staticmethod
    def suggest_elevation_from_lat_lon(sample: Dict[str, str]) -> Optional[str]:
        """Suggest an elevation for a sample based on its lat_lon."""
        logger = get_logger(__name__)
        if settings.google_map_api_key is None:
            logger.warning("Google Map API key is not set. Cannot provide an elevation suggestion.")
            return None
        lat_lon = sample.get("lat_lon", None)
        if lat_lon is None:
            return None
        lat_lon_split = re.split("[, ]+", lat_lon)
        if len(lat_lon_split) == 2:
            try:
                lat, lon = map(float, lat_lon_split)

                elev = nmdc_geoloc_tools.elevation((lat, lon), settings.google_map_api_key)
                return f"{elev:.2f}"
            except ValueError:
                # This could happen if the lat_lon string is not parseable as a float
                # or nmdc_geoloc_tools determined they are invalid values. In either case,
                # just don't suggest an elevation.
                pass
        return None

    @staticmethod
    def get_suggestions_from_study_information(submission: SubmissionMetadataSchema) -> dict:
        """Get suggestions based on study-level information from a submission"""

        # When run_recommendation_pipeline is available via `nmdc-metadata-suggestor-ai-tool`:
        # run_recommendation_pipeline(submission.model_dump())

        # For now, return a mock value:
        return {
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
