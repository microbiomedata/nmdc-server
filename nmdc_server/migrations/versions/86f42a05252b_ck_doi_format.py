"""empty message

Revision ID: 86f42a05252b
Revises: ffaec255fe68
Create Date: 2022-10-27 16:44:51.540940

"""
from typing import Optional

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "86f42a05252b"
down_revision: Optional[str] = "ffaec255fe68"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    # drop FK constraints for tables that point to doi_info
    op.drop_constraint(
        "fk_study_doi_doi_info",
        "study",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_publication_doi_doi_info",
        "publication",
        type_="foreignkey",
    )

    # transform DOIs to standardized format
    op.execute(r"UPDATE study SET doi = substring(doi FROM '10.\d{4,9}/[-._;()/\:a-zA-Z0-9]+')")
    op.execute(
        r"UPDATE publication SET doi = substring(doi FROM '10.\d{4,9}/[-._;()/\:a-zA-Z0-9]+')"
    )
    op.execute(r"UPDATE doi_info SET id = substring(id FROM '10.\d{4,9}/[-._;()/\:a-zA-Z0-9]+')")

    # add CHECK constraint for standardized DOI format
    op.create_check_constraint(
        "ck_doi_format",
        "doi_info",
        r"id ~* '^10.\d{4,9}/[-._;()/:a-zA-Z0-9]+$'",
    )

    # add back FK constraints for tables that point to doi_info
    op.create_foreign_key(
        "fk_publication_doi_doi_info",
        "publication",
        "doi_info",
        ["doi"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_study_doi_doi_info",
        "study",
        "doi_info",
        ["doi"],
        ["id"],
    )


def downgrade():
    op.drop_constraint("ck_doi_format", "doi_info", type_="check")
