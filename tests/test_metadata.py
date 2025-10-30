from nmdc_server.metadata import SampleMetadataSuggester


def test_sample_metadata_suggester_elevation():
    suggester = SampleMetadataSuggester()

    # Test with valid lat_lon
    sample = {"lat_lon": "37.875766 -122.248580"}
    elevation = suggester.suggest_elevation_from_lat_lon(sample)
    assert elevation == "16.00"

    # Be tolerant of a comma separator
    sample = {"lat_lon": "37.875766, -122.248580"}
    elevation = suggester.suggest_elevation_from_lat_lon(sample)
    assert elevation == "16.00"

    # Don't return a suggestion when lat_lon is missing
    sample = {}
    elevation = suggester.suggest_elevation_from_lat_lon(sample)
    assert elevation is None

    # Don't return a suggestion when lat_lon is invalid
    sample = {"lat_lon": "91.0 -122.248580"}
    elevation = suggester.suggest_elevation_from_lat_lon(sample)
    assert elevation is None

    sample = {"lat_lon": "no good"}
    elevation = suggester.suggest_elevation_from_lat_lon(sample)
    assert elevation is None

    sample = {"lat_lon": "0 0 0"}
    elevation = suggester.suggest_elevation_from_lat_lon(sample)
    assert elevation is None
