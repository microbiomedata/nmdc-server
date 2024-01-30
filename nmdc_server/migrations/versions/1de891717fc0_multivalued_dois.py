"""multivalued DOIs

Revision ID: 1de891717fc0
Revises: dad555bb9212
Create Date: 2023-08-23 19:22:15.660679

"""

from typing import Optional

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "1de891717fc0"
down_revision: Optional[str] = "dad555bb9212"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "study_doi_association",
        sa.Column("study_id", sa.String(), nullable=False),
        sa.Column("doi_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["doi_id"], ["doi_info.id"], name=op.f("fk_study_doi_association_doi_id_doi_info")
        ),
        sa.ForeignKeyConstraint(
            ["study_id"], ["study.id"], name=op.f("fk_study_doi_association_study_id_study")
        ),
        sa.PrimaryKeyConstraint("study_id", "doi_id", name=op.f("pk_study_doi_association")),
    )
    op.drop_table("study_publication")
    op.drop_table("publication")

    doitype = postgresql.ENUM("AWARD", "DATASET", "PUBLICATION", name="doitype")
    doitype.create(op.get_bind())

    op.add_column(
        "doi_info",
        sa.Column(
            "doi_type", sa.Enum("AWARD", "DATASET", "PUBLICATION", name="doitype"), nullable=True
        ),
    )
    op.drop_constraint("fk_study_doi_doi_info", "study", type_="foreignkey")
    op.drop_column("study", "doi")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("study", sa.Column("doi", sa.VARCHAR(), autoincrement=False, nullable=True))
    op.create_foreign_key("fk_study_doi_doi_info", "study", "doi_info", ["doi"], ["id"])
    op.drop_column("doi_info", "doi_type")
    op.create_table(
        "study_publication",
        sa.Column("study_id", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("publication_id", postgresql.UUID(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(
            ["publication_id"],
            ["publication.id"],
            name="fk_study_publication_publication_id_publication",
        ),
        sa.ForeignKeyConstraint(
            ["study_id"], ["study.id"], name="fk_study_publication_study_id_study"
        ),
        sa.PrimaryKeyConstraint("study_id", "publication_id", name="pk_study_publication"),
    )
    op.create_table(
        "publication",
        sa.Column("id", postgresql.UUID(), autoincrement=False, nullable=False),
        sa.Column("doi", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(["doi"], ["doi_info.id"], name="fk_publication_doi_doi_info"),
        sa.PrimaryKeyConstraint("id", name="pk_publication"),
        sa.UniqueConstraint("doi", name="uq_publication_doi"),
    )
    op.drop_table("study_doi_association")
    # ### end Alembic commands ###
