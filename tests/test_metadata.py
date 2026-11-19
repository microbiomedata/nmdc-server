from types import SimpleNamespace
from unittest.mock import ANY, Mock

import nmdc_server.metadata as metadata
from nmdc_server.metadata import ElevationSuggester


def test_elevation_suggester():
    suggester = ElevationSuggester()

    # Test with valid lat_lon
    sample = {"lat_lon": "37.875766 -122.248580"}
    s = suggester.suggest(sample)
    assert len(s) == 1
    assert s[0].slot == "elev"
    assert s[0].value == "16.00"

    # Be tolerant of a comma separator
    sample = {"lat_lon": "37.875766, -122.248580"}
    s = suggester.suggest(sample)
    assert len(s) == 1
    assert s[0].slot == "elev"
    assert s[0].value == "16.00"

    # Don't return a suggestion when lat_lon is missing
    sample = {}
    s = suggester.suggest(sample)
    assert s == []

    # Don't return a suggestion when lat_lon is invalid
    sample = {"lat_lon": "91.0 -122.248580"}
    s = suggester.suggest(sample)
    assert s == []

    sample = {"lat_lon": "no good"}
    s = suggester.suggest(sample)
    assert s == []

    sample = {"lat_lon": "0 0 0"}
    s = suggester.suggest(sample)
    assert s == []


def test_study_suggestions_pass_submission_and_sample_set(monkeypatch):
    submission = SimpleNamespace(model_dump=lambda: {"submission": "data"})
    sample_set = SimpleNamespace(
        model_dump=lambda: {"sample_set": "data"},
        sample_data=SimpleNamespace(data={}),
    )
    run_pipeline = Mock(return_value=SimpleNamespace(metadata_fields=[]))
    monkeypatch.setattr(metadata.settings, "llm_service_account_credentials_file", "credentials")
    monkeypatch.setattr(metadata, "LLMClient", Mock(return_value=object()))
    monkeypatch.setattr(metadata, "run_recommendation_pipeline", run_pipeline)

    suggestions = metadata.SampleMetadataSuggester().get_suggestions_from_study_information(
        interface_tab="sample",
        sample_data_slot=None,
        submission=submission,
        sample_set=sample_set,
    )

    assert suggestions == []
    run_pipeline.assert_called_once_with(
        submission_object={"submission": "data"},
        sample_set_object={"sample_set": "data"},
        llm_client=ANY,
        interface_name="sample",
    )
