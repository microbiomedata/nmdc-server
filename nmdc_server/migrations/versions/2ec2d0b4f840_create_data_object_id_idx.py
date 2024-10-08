"""Create index on column `data_object_id` for table `bulk_download_data_object`

Revision ID: 2ec2d0b4f840
Revises: 5fb9910ca8e6
Create Date: 2024-10-10 16:48:37.051479

"""

from typing import Optional

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2ec2d0b4f840"
down_revision: Optional[str] = "5fb9910ca8e6"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(
        "bulk_download_data_object_id_idx",
        "bulk_download_data_object",
        ["data_object_id"],
        unique=False,
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index("bulk_download_data_object_id_idx", table_name="bulk_download_data_object")
    # ### end Alembic commands ###
