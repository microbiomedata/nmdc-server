"""Add study_name and template columns to submission_metadata

Revision ID: 0ff690fb929d
Revises: c0b36f8dc4b8
Create Date: 2024-08-01 16:01:05.023371

"""

from typing import Optional

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import column, table

# revision identifiers, used by Alembic.
revision: str = "0ff690fb929d"
down_revision: Optional[str] = "c0b36f8dc4b8"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("submission_metadata", sa.Column("study_name", sa.String(), nullable=True))
    op.add_column(
        "submission_metadata",
        sa.Column("templates", JSONB(astext_type=sa.Text()), nullable=True),  # type:ignore
    )
    submission_metadata = table(
        "submission_metadata",
        column("id", sa.String),
        column("metadata_submission", JSONB),
        column("study_name", sa.String),
        column("templates", JSONB),
    )

    connection = op.get_bind()
    submissions = connection.execute(
        sa.select([submission_metadata.c.id, submission_metadata.c.metadata_submission])
    )

    for submission in submissions:
        study_name = submission.metadata_submission["studyForm"].get("studyName")
        templates = submission.metadata_submission.get("templates")
        if study_name:
            connection.execute(
                submission_metadata.update()
                .where(submission_metadata.c.id == submission.id)
                .values(study_name=study_name)
            )
        if templates:
            connection.execute(
                submission_metadata.update()
                .where(submission_metadata.c.id == submission.id)
                .values(templates=templates)
            )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("submission_metadata", "templates")
    op.drop_column("submission_metadata", "study_name")
    # ### end Alembic commands ###