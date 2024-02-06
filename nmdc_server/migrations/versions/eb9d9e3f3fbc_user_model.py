"""user_logins_model

Revision ID: eb9d9e3f3fbc
Revises: 780ab86a4f27
Create Date: 2022-06-09 16:03:35.013157

"""

from typing import Optional

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "eb9d9e3f3fbc"
down_revision: Optional[str] = "780ab86a4f27"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
    op.create_table(
        "user_logins",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("orcid", sa.String(), nullable=False),
        sa.Column("name", sa.String()),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.sql.False_()),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_logins")),
    )
    op.add_column(
        "submission_metadata", sa.Column("author_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        op.f("fk_submission_metadata_author_id_user_logins"),
        "submission_metadata",
        "user_logins",
        ["author_id"],
        ["id"],
    )
    op.execute(
        (
            """
                insert into user_logins(orcid, name)
                    select author_orcid, '' from submission_metadata
                    UNION
                    select orcid, '' from file_download
                    UNION
                    select orcid, '' from bulk_download
            """
        )
    )
    op.execute(
        (
            """
            UPDATE submission_metadata
            SET author_id = u.id
            FROM user_logins as u
            WHERE submission_metadata.author_orcid = u.orcid
            """
        )
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(
        op.f("fk_submission_metadata_author_id_user_logins"),
        "submission_metadata",
        type_="foreignkey",
    )
    op.drop_column("submission_metadata", "author_id")
    op.drop_table("user_logins")
    # ### end Alembic commands ###
