import pytest
from linkml_runtime.linkml_model.meta import PermissibleValue
from nmdc_schema.nmdc import MetadataBadgeEnum
from pydantic import ValidationError

from nmdc_server.schemas import METADATA_BADGE_VALUES, BiosampleBase


def test_metadata_badge_values_are_generated_from_nmdc_schema():
    expected = [
        value.text
        for value in vars(MetadataBadgeEnum).values()
        if isinstance(value, PermissibleValue)
    ]

    assert METADATA_BADGE_VALUES == expected


def test_biosample_accepts_metadata_badges():
    biosample = BiosampleBase(
        id="nmdc:bsm-00-000000",
        study_id="nmdc:sty-00-000000",
        badges=METADATA_BADGE_VALUES,
    )

    assert biosample.badges == METADATA_BADGE_VALUES


@pytest.mark.parametrize(
    "badges",
    [
        ["not_a_badge"],
        [METADATA_BADGE_VALUES[0], METADATA_BADGE_VALUES[0]],
        METADATA_BADGE_VALUES + [METADATA_BADGE_VALUES[0]],
    ],
)
def test_biosample_rejects_invalid_metadata_badges(badges):
    with pytest.raises(ValidationError):
        BiosampleBase(
            id="nmdc:bsm-00-000000",
            study_id="nmdc:sty-00-000000",
            badges=badges,
        )
