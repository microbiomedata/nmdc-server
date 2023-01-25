"""multi-tab metadata_submission format

Revision ID: 23e0702d2321
Revises: ae7a3eba08c5
Create Date: 2023-01-18 00:25:23.881413

"""
import json
import pathlib

from typing import Optional
from uuid import uuid4

from alembic import op
from sqlalchemy import Column, orm
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base

from nmdc_server.models import SubmissionMetadata

# revision identifiers, used by Alembic.
revision: str = '23e0702d2321'
down_revision: Optional[str] = 'ae7a3eba08c5'
branch_labels: Optional[str] = None
depends_on: Optional[str] = None

Base = declarative_base()

# This is defined here instead importing from nmdc_server.models to make it
# resilient against future changes to SubmissionMetadata.
class SubmissionMetadata(Base):
    __tablename__ = "submission_metadata"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    metadata_submission = Column(JSONB, nullable=False)


# Likewise this JSON document was built from the submission schema, but we 
# don't link to the checked-in schema file to make this migration continue 
# to work correctly if the schema changes.
# See: https://gist.github.com/pkalita-lbl/3d897bc0b50fa6f56593caacc95b617b
DIR = pathlib.Path(__file__).parent
with open(DIR / 'multi_tab_metadata_submission_format_slot_lookup.json', 'r') as in_file:
    SLOT_TITLE_MAP = json.load(in_file)


def upgrade():
    session = orm.Session(bind=op.get_bind())
    mappings = []
    for submission_metadata in session.query(SubmissionMetadata):
        metadata_submission = submission_metadata.metadata_submission

        template = metadata_submission['template']
        sample_data = metadata_submission['sampleData']
        package_name = metadata_submission['packageName']

        converted_sample_data = {}
        common_column_data = {}

        if isinstance(sample_data, dict):
            continue

        for row in sample_data[2:]:
            converted_row = {}
            for col_num, value in enumerate(row):
                col_title = sample_data[1][col_num]
                if not value:
                    continue

                col_classes = SLOT_TITLE_MAP[col_title]
                if len(col_classes) == 0:
                    print(f'WARNING: no classes found for column "{col_title}"')

                elif len(col_classes) == 1:
                    col_class, col_slot = list(col_classes.items())[0]
                    if col_class not in converted_row:
                        converted_row[col_class] = {}
                    converted_row[col_class][col_slot] = value

                elif 'dh_mutliview_common_columns' in col_classes:
                    col_slot = col_classes['dh_mutliview_common_columns']
                    common_column_data[col_slot] = value

                elif package_name in col_classes:
                    col_slot = col_classes[package_name]
                    if package_name not in converted_row:
                        converted_row[package_name] = {}
                    converted_row[package_name][col_slot] = value

                else:
                    print(f'WARNING: could not determine single template for column "{col_title}"')
                    
            for template in converted_row.values():
                template.update(common_column_data)

            for key, template in converted_row.items():
                if key not in converted_sample_data:
                    converted_sample_data[key] = []
                converted_sample_data[key].append(template)

        metadata_submission["_oldSampleData"] = sample_data
        metadata_submission["sampleData"] = converted_sample_data
        mappings.append({"id": submission_metadata.id, "metadata_submission": metadata_submission})

    session.bulk_update_mappings(SubmissionMetadata, mappings)
    session.commit()


def downgrade():
    session = orm.Session(bind=op.get_bind())
    mappings = []
    for submission_metadata in session.query(SubmissionMetadata):
        metadata_submission = submission_metadata.metadata_submission

        if "_oldSampleData" not in metadata_submission:
            continue

        old_sample_data = metadata_submission["_oldSampleData"]
        metadata_submission["sampleData"] = old_sample_data
        del metadata_submission["_oldSampleData"]

        mappings.append({"id": submission_metadata.id, "metadata_submission": metadata_submission})

    session.bulk_update_mappings(SubmissionMetadata, mappings)
    session.commit()
