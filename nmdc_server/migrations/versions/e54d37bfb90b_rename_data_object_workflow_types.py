"""Rename data object workflow types

The Berkeley schema migration changed a number of workflow type names. Even though
the `data_object` table is truncated at the start of the ingest process, the old
workflow types were being introduced by a merge operation from the live database
to the ingest database.

See also: https://github.com/microbiomedata/nmdc-server/issues/1415

Revision ID: e54d37bfb90b
Revises: 2ec2d0b4f840
Create Date: 2024-10-11 18:06:08.521445

"""

from typing import Optional

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import column, table

# revision identifiers, used by Alembic.
revision: str = "e54d37bfb90b"
down_revision: Optional[str] = "2ec2d0b4f840"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


WORKFLOW_TYPE_MAP = [
    {
        "old": "nmdc:MAGsAnalysisActivity",
        "new": "nmdc:MagsAnalysis",
    },
    {
        "old": "nmdc:MetabolomicsAnalysisActivity",
        "new": "nmdc:MetabolomicsAnalysis",
    },
    {
        "old": "nmdc:MetaProteomicAnalysis",
        "new": "nmdc:MetaproteomicAnalysis",
    },
    {
        "old": "nmdc:metaT",
        "new": "nmdc:MetatranscriptomeAnalysis",
    },
    {
        "old": "nmdc:NomAnalysisActivity",
        "new": "nmdc:NomAnalysis",
    },
    {
        "old": "nmdc:ReadbasedAnalysis",
        "new": "nmdc:ReadBasedTaxonomyAnalysis",
    },
    {
        "old": "nmdc:ReadQCAnalysisActivity",
        "new": "nmdc:ReadQcAnalysis",
    },
]


def upgrade():
    data_object = table("data_object", column("workflow_type", sa.String))
    for mapping in WORKFLOW_TYPE_MAP:
        op.execute(
            data_object.update()
            .where(data_object.c.workflow_type == mapping["old"])
            .values(workflow_type=mapping["new"])
        )


def downgrade():
    data_object = table("data_object", column("workflow_type", sa.String))
    for mapping in WORKFLOW_TYPE_MAP:
        op.execute(
            data_object.update()
            .where(data_object.c.workflow_type == mapping["new"])
            .values(workflow_type=mapping["old"])
        )
