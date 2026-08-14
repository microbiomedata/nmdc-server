"""Rename sequence data slots in sample sets

As introduced by nmdc-submission-schema v11.23.0:

metagenome_sequencing_interleaved_data -> dna_sequencing_interleaved_data
metagenome_sequencing_non_interleaved_data -> dna_sequencing_non_interleaved_data
metatranscriptome_sequencing_interleaved_data -> rna_sequencing_interleaved_data
metatranscriptome_sequencing_non_interleaved_data -> rna_sequencing_non_interleaved_data

See also: https://github.com/microbiomedata/submission-schema/pull/474

Revision ID: 6a181e611245
Revises: 3b9e6e16c449
Create Date: 2026-08-14 17:06:47.238022

"""

from collections.abc import Iterable
from typing import Optional

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6a181e611245"
down_revision: Optional[str] = "3b9e6e16c449"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


RENAMED_SLOTS = (
    (
        "metagenome_sequencing_interleaved_data",
        "dna_sequencing_interleaved_data",
    ),
    (
        "metagenome_sequencing_non_interleaved_data",
        "dna_sequencing_non_interleaved_data",
    ),
    (
        "metatranscriptome_sequencing_interleaved_data",
        "rna_sequencing_interleaved_data",
    ),
    (
        "metatranscriptome_sequencing_non_interleaved_data",
        "rna_sequencing_non_interleaved_data",
    ),
)


RENAME_SLOT = sa.text("""
    UPDATE submission_sample_set
    SET sample_data = jsonb_set(
        sample_data #- CAST(ARRAY['data', :source_name] AS text[]),
        CAST(ARRAY['data', :destination_name] AS text[]),
        sample_data #> CAST(ARRAY['data', :source_name] AS text[]),
        true
    )
    WHERE sample_data -> 'data' ? :source_name
    """)


def _rename_slots(renames: Iterable[tuple[str, str]]) -> None:
    for source_name, destination_name in renames:
        op.execute(
            RENAME_SLOT.bindparams(
                source_name=source_name,
                destination_name=destination_name,
            )
        )


def upgrade():
    _rename_slots(RENAMED_SLOTS)


def downgrade():
    _rename_slots((new_name, old_name) for old_name, new_name in RENAMED_SLOTS)
