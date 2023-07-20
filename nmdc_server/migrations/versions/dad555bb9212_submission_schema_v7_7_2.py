"""submission schema v7.7.2

* Changes the permissible values of the enum in the cur_land_use
slot. See https://github.com/microbiomedata/sheets_and_friends/issues/60

Revision ID: dad555bb9212
Revises: af8b2e3c91b2
Create Date: 2023-07-14 21:12:10.113468

"""
from typing import Optional
from uuid import uuid4

from alembic import op
from sqlalchemy import Column, orm
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base

# revision identifiers, used by Alembic.
revision: str = "dad555bb9212"
down_revision: Optional[str] = "af8b2e3c91b2"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


CUR_LAND_USE_RENAMES = [
    # (old name, new name)
    ("conifers (e.g. pine,spruce,fir,cypress)", "conifers"),
    ("crop trees (nuts,fruit,christmas trees,nursery trees)", "crop trees"),
    ("hardwoods (e.g. oak,hickory,elm,aspen)", "hardwoods"),
    ("horticultural plants (e.g. tulips)", "horticultural plants"),
    ("marshlands (grass,sedges,rushes)", "marshlands"),
    ("meadows (grasses,alfalfa,fescue,bromegrass,timothy)", "meadows"),
    ("pastureland (grasslands used for livestock grazing)", "pastureland"),
    ("rainforest (evergreen forest receiving greater than 406 cm annual rainfall)", "rainforest"),
    ("shrub crops (blueberries,nursery ornamentals,filberts)", "shrub crops"),
    ("shrub land (e.g. mesquite,sage-brush,creosote bush,shrub oak,eucalyptus)", "shrub land"),
    (
        "successional shrub land (tree saplings,hazels,sumacs,chokecherry,"
        "shrub dogwoods,blackberries)",
        "successional shrub land",
    ),
    ("swamp (permanent or semi-permanent water body dominated by woody plants)", "swamp"),
    ("tropical (e.g. mangrove,palms)", "tropical"),
    ("tundra (mosses,lichens)", "tundra"),
    ("vine crops (grapes)", "vine crops"),
]


Base = declarative_base()


class SubmissionMetadata(Base):
    __tablename__ = "submission_metadata"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    metadata_submission = Column(JSONB, nullable=False)


def rename(slot, rename_map):
    session = orm.Session(bind=op.get_bind())
    mappings = []
    for submission_metadata in session.query(SubmissionMetadata):
        metadata_submission = submission_metadata.metadata_submission

        if isinstance(metadata_submission, list):
            continue

        sample_data = metadata_submission.get("sampleData")

        if sample_data is None or not isinstance(sample_data, dict):
            print(f"WARNING: sampleData not in migratable format for {submission_metadata.id}")
            continue

        for tab in sample_data.values():
            for row in tab:
                value = row.get(slot)
                if value in rename_map:
                    row[slot] = rename_map[value]

        mappings.append({"id": submission_metadata.id, "metadata_submission": metadata_submission})
    session.bulk_update_mappings(SubmissionMetadata, mappings)
    session.commit()


def upgrade():
    upgrade_map = dict(CUR_LAND_USE_RENAMES)
    rename("cur_land_use", upgrade_map)


def downgrade():
    downgrade_map = dict((t[1], t[0]) for t in CUR_LAND_USE_RENAMES)
    rename("cur_land_use", downgrade_map)
