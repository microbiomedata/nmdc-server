"""multi-tab metadata_submission format

Revision ID: 23e0702d2321
Revises: ae7a3eba08c5
Create Date: 2023-01-18 00:25:23.881413

"""
import collections
import json
import pathlib
from typing import Any, Dict, List, Optional
from uuid import uuid4

from alembic import op
from sqlalchemy import Column, orm
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base

# revision identifiers, used by Alembic.
revision: str = "23e0702d2321"
down_revision: Optional[str] = "ae7a3eba08c5"
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
with open(DIR / "multi_tab_metadata_submission_format_slot_lookup.json", "r") as in_file:
    SLOT_TITLE_MAP = json.load(in_file)


PACKAGE_CLASSES = {
    "built environment": "built_env",
    "hydrocarbon resources-cores": "hcr-cores",
    "hydrocarbon resources-fluids_swabs": "hcr-fluids-swabs",
    "microbial mat_biofilm": "biofilm",
    "miscellaneous natural or artificial environment": "misc-envs",
}

EMSL = "emsl"
JGI_MG = "jgi_mg"
JGI_MT = "jgi_mt"


def upgrade_templates(omics_processing_types, environmental_package):
    templates = [environmental_package]
    if (
        "mp-emsl" in omics_processing_types
        or "mb-emsl" in omics_processing_types
        or "nom-emsl" in omics_processing_types
    ):
        templates.append(EMSL)

    if "mg-jgi" in omics_processing_types:
        templates.append(JGI_MG)

    if "mt-jgi" in omics_processing_types:
        templates.append(JGI_MT)

    return templates


def downgrade_templates(omics_processing_types, environmental_package):
    variation_map = {
        "emsl": {"mp-emsl", "mb-emsl", "nom-emsl"},
        "jgi_mg": {"mg-jgi"},
        "emsl_jgi_mg": {"mp-emsl", "mb-emsl", "nom-emsl", "mg-jgi"},
        "jgi_mt": {"mt-jgi"},
        "emsl_jgi_mt": {"mp-emsl", "mb-emsl", "nom-emsl", "mt-jgi"},
        "jgi_mg_mt": {"mg-jgi", "mt-jgi"},
        "emsl_jgi_mg_mt": {"mp-emsl", "mb-emsl", "nom-emsl", "mg-jgi", "mt-jgi"},
    }
    variant = next(
        (v for v, s in variation_map.items() if all(o in s for o in omics_processing_types)), None
    )
    template = environmental_package
    if variant:
        template += f"_{variant}"

    return template


def upgrade():  # noqa: C901
    session = orm.Session(bind=op.get_bind())
    mappings = []
    for submission_metadata in session.query(SubmissionMetadata):
        metadata_submission = submission_metadata.metadata_submission

        if isinstance(metadata_submission, list):
            continue

        sample_data = metadata_submission["sampleData"]
        package_name = metadata_submission["packageName"]
        package_class = PACKAGE_CLASSES.get(package_name, package_name)
        template = metadata_submission["template"]

        converted_sample_data: Dict[str, List[Any]] = collections.defaultdict(list)
        common_column_data: Dict[str, Any] = {}

        # If sample_data is in the list-of-lists format, upgrade it to the dict format
        if isinstance(sample_data, list):
            for row in sample_data[2:]:
                converted_row: Dict[str, Dict[str, Any]] = collections.defaultdict(dict)
                for col_num, value in enumerate(row):
                    col_title = sample_data[1][col_num]
                    if not value:
                        continue

                    col_classes = SLOT_TITLE_MAP[col_title]
                    if len(col_classes) == 0:
                        print(f'WARNING: no classes found for column "{col_title}" '
                              f'in {submission_metadata.id}')

                    elif len(col_classes) == 1:
                        col_class, col_slot = list(col_classes.items())[0]
                        converted_row[col_class][col_slot] = value

                    elif "dh_mutliview_common_columns" in col_classes:
                        col_slot = col_classes["dh_mutliview_common_columns"]
                        common_column_data[col_slot] = value

                    elif package_class in col_classes:
                        col_slot = col_classes[package_class]
                        converted_row[package_class][col_slot] = value

                    elif EMSL in col_class and "emsl" in template:
                        col_slot = col_classes[EMSL]
                        converted_row[EMSL][col_slot] = value

                    elif JGI_MG in col_class and "jgi_mg" in template:
                        col_slot = col_classes[JGI_MG]
                        converted_row[JGI_MG][col_slot] = value

                    elif JGI_MT in col_classes and (
                        "jgi_mt" in template or "jgi_mg_mt" in template
                    ):
                        col_slot = col_classes[JGI_MT]
                        converted_row[JGI_MT][col_slot] = value

                    else:
                        print(f'WARNING: could not determine template for column "{col_title}" '
                              f'in {submission_metadata.id}')

                for row in converted_row.values():
                    row.update(common_column_data)

                for key, row in converted_row.items():
                    suffixed_key = f"{key}_data"
                    converted_sample_data[suffixed_key].append(row)

            metadata_submission["_oldSampleData"] = sample_data
            metadata_submission["sampleData"] = converted_sample_data

        # if template is in metadata_submission, drop it in favor of templates
        if "template" in metadata_submission:
            omics_processing_types = metadata_submission.get("multiOmicsForm", {}).get(
                "omicsProcessingTypes", []
            )
            environmental_package = metadata_submission.get("packageName", "soil")

            metadata_submission["templates"] = upgrade_templates(
                omics_processing_types, environmental_package
            )
            del metadata_submission["template"]

        mappings.append({"id": submission_metadata.id, "metadata_submission": metadata_submission})

    session.bulk_update_mappings(SubmissionMetadata, mappings)
    session.commit()


def downgrade():
    session = orm.Session(bind=op.get_bind())
    mappings = []
    for submission_metadata in session.query(SubmissionMetadata):
        metadata_submission = submission_metadata.metadata_submission

        if isinstance(metadata_submission, list):
            continue

        if "_oldSampleData" in metadata_submission:
            old_sample_data = metadata_submission["_oldSampleData"]
            metadata_submission["sampleData"] = old_sample_data
            del metadata_submission["_oldSampleData"]

        if "templates" in metadata_submission:
            omics_processing_types = metadata_submission.get("multiOmicsForm", {}).get(
                "omicsProcessingTypes", []
            )
            environmental_package = metadata_submission.get("packageName", "soil")

            metadata_submission["template"] = downgrade_templates(
                omics_processing_types, environmental_package
            )
            del metadata_submission["templates"]

        mappings.append({"id": submission_metadata.id, "metadata_submission": metadata_submission})

    session.bulk_update_mappings(SubmissionMetadata, mappings)
    session.commit()
