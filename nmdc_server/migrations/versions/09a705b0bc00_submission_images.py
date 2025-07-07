"""Add submission_images_object table.

The name of the table indicates that stores references to objects in the nmdc-submission-images
Google Cloud Storage bucket.

Each submission can have:
- Up to one PI headshot image
- Up to one primary study image
- Any number of additional study images

Therefore, this new table is referenced by two new foreign key columns in the submission_metadata
table (pi_image_name and primary_study_image_name) and by a new association table for the
additional study images (submission_study_image_association).

Revision ID: 09a705b0bc00
Revises: 997064dd504d
Create Date: 2025-07-07 18:40:50.493009

"""

from typing import Optional

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "09a705b0bc00"
down_revision: Optional[str] = "997064dd504d"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.create_table(
        "submission_images_object",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("size", sa.BigInteger(), nullable=False),
        sa.Column("content_type", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("name", name=op.f("pk_submission_images_object")),
    )

    op.create_table(
        "submission_study_image_association",
        sa.Column("submission_metadata_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("submission_images_object_name", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["submission_images_object_name"],
            ["submission_images_object.name"],
            name=op.f(
                "fk_submission_study_image_association_"
                + "submission_images_object_name_submission_images_object"
            ),
        ),
        sa.ForeignKeyConstraint(
            ["submission_metadata_id"],
            ["submission_metadata.id"],
            name=op.f(
                "fk_submission_study_image_association_submission_metadata_id_submission_metadata"
            ),
        ),
        sa.PrimaryKeyConstraint(
            "submission_metadata_id",
            "submission_images_object_name",
            name=op.f("pk_submission_study_image_association"),
        ),
    )

    op.add_column("submission_metadata", sa.Column("pi_image_name", sa.String(), nullable=True))
    op.add_column(
        "submission_metadata", sa.Column("primary_study_image_name", sa.String(), nullable=True)
    )
    op.create_foreign_key(
        op.f("fk_submission_metadata_primary_study_image_name_submission_images_object"),
        "submission_metadata",
        "submission_images_object",
        ["primary_study_image_name"],
        ["name"],
    )
    op.create_foreign_key(
        op.f("fk_submission_metadata_pi_image_name_submission_images_object"),
        "submission_metadata",
        "submission_images_object",
        ["pi_image_name"],
        ["name"],
    )


def downgrade():
    op.drop_constraint(
        op.f("fk_submission_metadata_pi_image_name_submission_images_object"),
        "submission_metadata",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_submission_metadata_primary_study_image_name_submission_images_object"),
        "submission_metadata",
        type_="foreignkey",
    )
    op.drop_column("submission_metadata", "primary_study_image_name")
    op.drop_column("submission_metadata", "pi_image_name")
    op.drop_table("submission_study_image_association")
    op.drop_table("submission_images_object")
