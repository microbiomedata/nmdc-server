"""Create `biosample_related_document` table

Revision ID: 6867009bb496
Revises: 87821b18f9e3
Create Date: 2026-02-26 08:56:09.654967

"""

from typing import Optional

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "6867009bb496"
down_revision: Optional[str] = "87821b18f9e3"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    # TODO: Consider using a many-to-many association table instead of storing `biosample_ids` here.
    op.create_table(
        "biosample_related_document",
        sa.Column(
            "id",
            sa.String(),
            nullable=False,
            primary_key=True,
            comment="The value in the document's 'id' field",
        ),
        sa.Column(
            "biosample_ids",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default=sa.text("'{}'"),  # in Postgres, "{}" represents an empty array
            comment="The IDs of all biosamples downstream of, upstream of, or representing the document",
        ),
        sa.Column(
            "high_level_type",
            sa.String(),
            nullable=False,
            comment="High-level type of the document (e.g., 'nmdc:WorkflowExecution')",
        ),
        sa.Column(
            "document",
            postgresql.JSONB(astext_type=sa.Text()),  # type: ignore[call-arg]
            nullable=False,
            comment="NMDC Schema-compliant document downstream of, upstream of, or representing the subject biosample",
        ),
        sa.Column(
            "downstream_neighbor_ids",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default=sa.text("'{}'"),  # in Postgres, "{}" represents an empty array
            comment="IDs of documents that are immediately downstream of the document",
        ),
    )
    # Create a GIN index on the "biosample_ids" array column in an attempt to speed up searches by its values.
    # Note: GIN indexes are designed for columns whose values are "composite" (e.g. arrays).
    #       Reference: https://www.postgresql.org/docs/current/gin.html
    op.create_index(
        index_name="ix_biosample_related_document_biosample_ids",
        table_name="biosample_related_document",
        columns=["biosample_ids"],
        postgresql_using="gin",
    )
    # Create an index on the "high_level_type" column in an attempt to speed up searches by its values.
    op.create_index(
        index_name="ix_biosample_related_document_high_level_type",
        table_name="biosample_related_document",
        columns=["high_level_type"],
    )
    # Create an index on the "type" JSON field in an attempt to speed up searches by its values.
    op.create_index(
        index_name="ix_biosample_related_document_document_type",
        table_name="biosample_related_document",
        columns=[sa.text("(document->>'type')")],
    )
    # Create a GIN index on the "downstream_neighbor_ids" array column in an attempt to speed up searches by its values.
    # Note: GIN indexes are designed for columns whose values are "composite" (e.g. arrays).
    #       Reference: https://www.postgresql.org/docs/current/gin.html
    op.create_index(
        index_name="ix_biosample_related_document_downstream_neighbor_ids",
        table_name="biosample_related_document",
        columns=["downstream_neighbor_ids"],
        postgresql_using="gin",
    )


def downgrade():
    op.drop_index(
        index_name="ix_biosample_related_document_biosample_ids",
        table_name="biosample_related_document",
    )
    op.drop_index(
        index_name="ix_biosample_related_document_high_level_type",
        table_name="biosample_related_document",
    )
    op.drop_index(
        index_name="ix_biosample_related_document_document_type",
        table_name="biosample_related_document",
    )
    op.drop_index(
        index_name="ix_biosample_related_document_downstream_neighbor_ids",
        table_name="biosample_related_document",
    )
    op.drop_table("biosample_related_document")
