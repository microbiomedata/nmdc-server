"""add name, created, and date_last_modified to submission_sample_set

Revision ID: 3ead3f3357a2
Revises: 6274a27c66dd
Create Date: 2026-05-29 16:00:46.605688

"""

from typing import Optional

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import column, table

# revision identifiers, used by Alembic.
revision: str = "3ead3f3357a2"
down_revision: Optional[str] = "6274a27c66dd"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    # Add the columns as nullable to allow for backfilling data before enforcing non-null constraints.
    op.add_column("submission_sample_set", sa.Column("name", sa.String(), nullable=True))
    op.add_column("submission_sample_set", sa.Column("created", sa.DateTime(), nullable=True))
    op.add_column(
        "submission_sample_set", sa.Column("date_last_modified", sa.DateTime(), nullable=True)
    )

    # Define the relevant parts of the tables to use in the data migration.
    submission_metadata = table(
        "submission_metadata",
        column("id", postgresql.UUID),
        column("created", sa.DateTime),
        column("date_last_modified", sa.DateTime),
    )
    submission_sample_set = table(
        "submission_sample_set",
        column("id", postgresql.UUID),
        column("submission_metadata_id", postgresql.UUID),
        column("name", sa.String),
        column("created", sa.DateTime),
        column("date_last_modified", sa.DateTime),
    )

    # Select existing sample sets along with their associated submission.
    connection = op.get_bind()
    sample_sets = connection.execute(
        sa.select(
            submission_sample_set.c.id,  # type: ignore[arg-type]
            submission_metadata.c.created,
            submission_metadata.c.date_last_modified,  # type: ignore[arg-type]
        ).select_from(
            submission_sample_set.join(
                submission_metadata,
                submission_sample_set.c.submission_metadata_id == submission_metadata.c.id,
            )
        )
    )

    # Backfill the new columns for existing sample sets. The name is generated based on the
    # creation date of the associated submission. The created and date_last_modified values are
    # copied from the associated submission.
    for sample_set in sample_sets:
        created = sample_set.created
        connection.execute(
            submission_sample_set.update()
            .where(submission_sample_set.c.id == sample_set.id)
            .values(
                name=f"Sample Set {created.date().isoformat()}",
                created=created,
                date_last_modified=sample_set.date_last_modified,
            )
        )

    # After backfilling data, alter the columns to set nullable=False to enforce that all sample
    # sets have these values.
    op.alter_column("submission_sample_set", "name", existing_type=sa.String(), nullable=False)
    op.alter_column("submission_sample_set", "created", existing_type=sa.DateTime(), nullable=False)
    op.alter_column(
        "submission_sample_set",
        "date_last_modified",
        existing_type=sa.DateTime(),
        nullable=False,
    )


def downgrade():
    op.drop_column("submission_sample_set", "date_last_modified")
    op.drop_column("submission_sample_set", "created")
    op.drop_column("submission_sample_set", "name")
