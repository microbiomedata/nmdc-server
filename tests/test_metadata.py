from nmdc_server.metadata import ElevationSuggester


def test_sample_metadata_suggester_elevation():
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
