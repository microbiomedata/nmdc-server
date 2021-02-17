"""add doi table

Revision ID: f1cd153d1a16
Revises: 7057e7745ce6
Create Date: 2021-02-17 15:40:31.316844

"""
from typing import Optional

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

from nmdc_server.ingest.doi import upsert_doi
from nmdc_server.models import Publication, Study

# revision identifiers, used by Alembic.
revision: str = "f1cd153d1a16"
down_revision: Optional[str] = "7057e7745ce6"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    db = Session(bind=op.get_bind())
    op.create_table(
        "doi_info",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("info", postgresql.JSONB(astext_type=sa.Text()), nullable=False),  # type: ignore
        sa.PrimaryKeyConstraint("id", name=op.f("pk_doi_info")),
    )
    for study in db.query(Study):
        upsert_doi(db, study.doi)

    for publication in db.query(Publication):
        upsert_doi(db, publication.doi)

    db.commit()
    op.create_foreign_key(
        op.f("fk_publication_doi_doi_info"), "publication", "doi_info", ["doi"], ["id"]
    )
    op.create_foreign_key(op.f("fk_study_doi_doi_info"), "study", "doi_info", ["doi"], ["id"])


def downgrade():
    op.drop_constraint(op.f("fk_study_doi_doi_info"), "study", type_="foreignkey")
    op.drop_constraint(op.f("fk_publication_doi_doi_info"), "publication", type_="foreignkey")
    op.drop_table("doi_info")
