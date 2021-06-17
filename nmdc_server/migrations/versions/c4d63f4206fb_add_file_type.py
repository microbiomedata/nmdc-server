"""add file type

Revision ID: c4d63f4206fb
Revises: 7f9314e44f22
Create Date: 2021-06-17 09:11:53.621740

"""
from typing import Optional

from alembic import op

from nmdc_server.ingest.data_object import file_type_map


# revision identifiers, used by Alembic.
revision: str = "c4d63f4206fb"
down_revision: Optional[str] = "7f9314e44f22"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    for name in sorted(file_type_map, key=lambda n: len(n), reverse=True):
        file_type = file_type_map[name]
        op.execute(
            f"""
            update data_object
            set file_type = '{file_type}'
            where name like '%{name}%' and file_type is null
        """
        )


def downgrade():
    pass
