from datetime import datetime
import json
from pathlib import Path
import re
from typing import Dict, List, Union

from alembic import command
from alembic.config import Config
from sqlalchemy.orm import Session
from typing_extensions import TypedDict

from nmdc_server import database, models, schemas
from nmdc_server.config import settings
from nmdc_server.database import Base, engine

HERE = Path(__file__).parent
DATA = HERE / "data"
date_re = re.compile(r"^\d{2}$")
# 23-FEB-18 01.10.55.869000000 PM
date_fmt = r"\d\d-[A-Z]+-\d\d \d\d\.\d\d\.\d\d\.\d+ [AP]M"


class Characteristic(TypedDict):
    name: str


class Annotation(TypedDict):
    has_characteristic: Characteristic
    has_raw_value: Union[str, int, float]


def create_tables():
    Base.metadata.create_all(engine)
    alembic_cfg = Config(str(HERE / "alembic.ini"))
    alembic_cfg.set_main_option("sqlalchemy.url", settings.database_uri)
    command.stamp(alembic_cfg, "head")


def coerce_value(value: Union[str, int, float]) -> schemas.AnnotationValue:
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, "%d-%b-%y %I.%M.%S.%f000 %p").isoformat()
        except ValueError:
            pass
    return value


def load_annotations(
    annotations: List[Annotation],
) -> Dict[str, schemas.AnnotationValue]:
    return {
        a["has_characteristic"]["name"]: coerce_value(a["has_raw_value"])
        for a in annotations
    }


def ingest_studies(db: Session):
    with (DATA / "study.json").open("r") as f:
        data = json.load(f)
    for study in data:
        study['annotations'] = load_annotations(study['annotations'])
        study_db = models.Study(**study)
        db.add(study_db)
    db.commit()


def ingest_projects(db: Session) -> Dict[str, str]:
    data_objects: Dict[str, str] = {}
    with (DATA / "omics_processing.json").open("r") as f:
        data = json.load(f)
    for p in data:
        assert len(p['part_of']) == 1
        project = {
            'id': p['id'],
            'name': p['name'],
            'study_id': p['part_of'][0]
        }
        for key in p.get('has_output', []):
            data_objects[key] = p['id']

        project['annotations'] = load_annotations(p['annotations'])
        project_db = models.Project(**project)
        db.add(project_db)
    db.commit()

    return data_objects


def ingest_biosamples(db: Session):
    with (DATA / "biosample.json").open("r") as f:
        data = json.load(f)
    for p in data:
        assert len(p['part_of']) == 1
        biosample = {
            'id': p['id'],
            'name': p['name'],
            'project_id': p['part_of'][0]
        }
        biosample['annotations'] = load_annotations(p['annotations'])
        biosample_db = models.Biosample(**biosample)
        db.add(biosample_db)
    db.commit()


def ingest_data_objects(db: Session, data_object_map: Dict[str, str]):
    with (DATA / "data_objects.json").open("r") as f:
        data = json.load(f)
    for p in data:
        data_object = {
            'id': p['id'],
            'name': p['name'],
            'project_id': data_object_map[p['id']]
        }
        data_object['annotations'] = load_annotations(p['annotations'])
        data_object_db = models.DataObject(**data_object)
        db.add(data_object_db)
    db.commit()


def main():
    create_tables()
    db = database.SessionLocal()
    ingest_studies(db)
    data_object_map = ingest_projects(db)
    ingest_biosamples(db)
    ingest_data_objects(db, data_object_map)


if __name__ == "__main__":
    main()
