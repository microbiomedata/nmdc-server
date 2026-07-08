"""Unit tests for ``nmdc_server.ingest.omics_processing.load_amplicon_data``.

``load_amplicon_data`` reads the amplicon slots ``target_gene`` and ``target_subfragment``
from the ``LibraryPreparation`` (a ``material_processing_set`` document) that produced one
of a data generation's inputs. Those two slots are *independent* optional slots in the NMDC
schema -- either, both, or neither may be present, and one does not require the other -- so
these tests exercise every combination (per review discussion on PR #2238).

The function takes the Mongo lookup as an injected callback, so no Mongo instance (or
mocking of one) is needed here: each test passes a stub callback that maps an input ID to a
canned ``LibraryPreparation`` document (returning ``None`` when there is no match).
"""

import doctest
from typing import Callable, Optional

import pytest

from nmdc_server.ingest import omics_processing
from nmdc_server.ingest.omics_processing import load_amplicon_data


def _stub_finder(
    documents_by_input_id: dict[str, dict],
) -> Callable[[str], Optional[dict]]:
    """Build a ``find_material_processing_having_id_in_output`` stub from a lookup table."""
    return lambda input_id: documents_by_input_id.get(input_id)


@pytest.mark.parametrize(
    ("description", "input_ids", "documents_by_input_id", "expected"),
    [
        # The four target_gene x target_subfragment presence combinations called out in
        # review (https://github.com/microbiomedata/nmdc-server/pull/2238). A real
        # LibraryPreparation document always carries at least an `id`, so the "neither
        # present" case is a non-empty document that simply lacks both slots.
        (
            "gene absent, subfragment absent",
            ["input_a"],
            {"input_a": {"id": "nmdc:libprep-1"}},
            {"target_gene": None, "target_subfragment": None},
        ),
        (
            "gene absent, subfragment present (independent of gene)",
            ["input_a"],
            {"input_a": {"target_subfragment": "V4"}},
            {"target_gene": None, "target_subfragment": "V4"},
        ),
        (
            "gene present, subfragment absent",
            ["input_a"],
            {"input_a": {"target_gene": "16S rRNA"}},
            {"target_gene": "16S rRNA", "target_subfragment": None},
        ),
        (
            "gene present, subfragment present",
            ["input_a"],
            {"input_a": {"target_gene": "16S rRNA", "target_subfragment": "V4"}},
            {"target_gene": "16S rRNA", "target_subfragment": "V4"},
        ),
        # target_subfragment's schema range is TextValue, which ingests as a
        # {"has_raw_value": ...} dict; the raw value is what gets stored.
        (
            "subfragment as TextValue dict is normalized to its raw value",
            ["input_a"],
            {
                "input_a": {
                    "target_gene": "16S rRNA",
                    "target_subfragment": {"has_raw_value": "V4"},
                }
            },
            {"target_gene": "16S rRNA", "target_subfragment": "V4"},
        ),
        (
            "subfragment as TextValue dict, gene absent (e.g. ITS region)",
            ["input_a"],
            {"input_a": {"target_subfragment": {"has_raw_value": "ITS1"}}},
            {"target_gene": None, "target_subfragment": "ITS1"},
        ),
        # No LibraryPreparation is found for the inputs.
        (
            "no LibraryPreparation matches the input",
            ["input_a"],
            {},
            {"target_gene": None, "target_subfragment": None},
        ),
        (
            "no input IDs",
            [],
            {},
            {"target_gene": None, "target_subfragment": None},
        ),
        # Multiple inputs whose LibraryPreparations each carry only one of the two
        # independent fields: scanning must not stop early, so both get collected.
        (
            "independent fields split across two inputs are both collected",
            ["input_a", "input_b"],
            {
                "input_a": {"target_gene": "16S rRNA"},
                "input_b": {"target_subfragment": "V4"},
            },
            {"target_gene": "16S rRNA", "target_subfragment": "V4"},
        ),
    ],
)
def test_load_amplicon_data(
    description: str,
    input_ids: list[str],
    documents_by_input_id: dict[str, dict],
    expected: dict[str, Optional[str]],
) -> None:
    obj: dict = {}
    load_amplicon_data(obj, input_ids, _stub_finder(documents_by_input_id))
    assert obj == expected, description


def test_load_amplicon_data_doctests() -> None:
    """The module's inline doctests must pass; run them here so CI enforces them too."""
    results = doctest.testmod(omics_processing)
    assert results.failed == 0
