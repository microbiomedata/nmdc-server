from datetime import datetime
import json
from pathlib import Path
import re
from typing import Any, Dict, List, Union
from urllib import request

from alembic import command
from alembic.config import Config
from sqlalchemy.orm import Session

from nmdc_server import crud, models, schemas
from nmdc_server.config import Settings
from nmdc_server.database import create_session, metadata

HERE = Path(__file__).parent
DATA = HERE / "data"
NOW = datetime.now().isoformat()
date_re = re.compile(r"^\d{2}$")
# 23-FEB-18 01.10.55.869000000 PM
date_fmt = r"\d\d-[A-Z]+-\d\d \d\d\.\d\d\.\d\d\.\d+ [AP]M"
envo_url = "http://purl.obolibrary.org/obo/envo.json"

JsonValueType = Dict[str, str]
JsonObjectType = Dict[str, Any]
AnnotatedObjectType = Dict[str, Any]


def coerce_id(id_: Union[str, int]) -> str:
    return str(id_)


def coerce_value(value: Union[str, int, float]) -> schemas.AnnotationValue:
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, "%d-%b-%y %I.%M.%S.%f000 %p").isoformat()
        except ValueError:
            pass
    return value


def extract_value(value: Union[JsonValueType, str]) -> Any:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return coerce_value(value["has_raw_value"])
    return value


def load_json_object(json_object: JsonObjectType) -> AnnotatedObjectType:
    return {k: extract_value(v) for k, v in json_object.items() if k != "type"}


def load_json_objects(json_file: Path) -> List[AnnotatedObjectType]:
    with json_file.open("r") as f:
        json_objects = json.load(f)
    return [load_json_object(o) for o in json_objects]


def load_common_fields(json_object: JsonObjectType, include_dates: bool = True) -> Dict[str, Any]:
    obj = {
        "id": coerce_id(json_object.pop("id")),
        "name": json_object.pop("name"),
        "description": json_object.pop("description", ""),
    }
    if include_dates:
        obj.update(
            {"add_date": json_object.pop("add_date"), "mod_date": json_object.pop("mod_date", NOW),}
        )
    return obj


def create_tables(db, settings):
    engine = db.bind
    metadata.create_all(engine)
    alembic_cfg = Config(str(HERE / "alembic.ini"))
    alembic_cfg.set_main_option("sqlalchemy.url", settings.database_uri)
    command.stamp(alembic_cfg, "head")

    db.query(models.DataObject).delete()
    db.query(models.Biosample).delete()
    db.query(models.Project).delete()
    db.query(models.StudyWebsite).delete()
    db.query(models.StudyPublication).delete()
    db.query(models.Website).delete()
    db.query(models.Publication).delete()
    db.query(models.Study).delete()


def populate_envo(db):
    with request.urlopen(envo_url) as r:
        envo_data = json.load(r)

    for graph in envo_data["graphs"]:
        for node in envo_data["nodes"]:
            id = node["id"].split("/")[-1]
            label = node.pop("lbl", "")
            db.add(models.EnvoTerm(id=id, label=label, data=node))


def ingest_studies(db: Session):
    with Path("study_additional.json").open("r") as f:
        data = json.load(f)

    additional_data = {f"gold:{d['id']}": d for d in data}

    studies = []
    data = load_json_objects(DATA / "gold_study.json")
    for raw_study in data:
        study = load_common_fields(raw_study)
        study["gold_description"] = study["description"]
        study[
            "description"
        ] = f"Principal investigator: {raw_study.pop('principal_investigator_name')}"
        study["publication_dois"] = [raw_study.pop("doi")]
        study["annotations"] = raw_study

        if study["id"] in additional_data:
            a = additional_data[study["id"]]
            study["name"] = a["proposal_title"]
            study["principal_investigator_websites"] = a["principal_investigator_websites"]
            study["publication_dois"].extend(a["publication_dois"])
            study["scientific_objective"] = a["scientific_objective"]

        studies.append(study)
        crud.create_study(db, schemas.StudyCreate(**study))
    db.commit()


def ingest_projects(db: Session) -> Dict[str, str]:
    data_objects: Dict[str, str] = {}
    projects = []

    for p in load_json_objects(DATA / "gold_omics_processing.json"):
        assert len(p["part_of"]) == 1
        project = load_common_fields(p)
        project["study_id"] = coerce_id(p.pop("part_of")[0])
        for key in p.pop("has_output", []):
            data_objects[coerce_id(key)] = project["id"]

        project["annotations"] = p
        projects.append(project)
        project_db = models.Project(**project)
        db.add(project_db)
    db.commit()

    return data_objects


def ingest_biosamples(db: Session):
    for p in load_json_objects(DATA / "biosample.json"):
        biosample = load_common_fields(p)
        assert len(p["part_of"]) == 1
        lat, lon = p.pop("lat_lon").split(" ")
        biosample.update(
            {
                "project_id": coerce_id(p.pop("part_of")[0]),
                "latitude": float(lat),
                "longitude": float(lon),
                "env_broad_scale": p.pop("env_broad_scale"),
                "env_local_scale": p.pop("env_local_scale"),
                "env_medium": p.pop("env_medium"),
                "annotations": p,
            }
        )

        if "depth" in biosample["annotations"]:
            biosample["depth"] = float(biosample["annotations"].pop("depth"))

        biosample_db = models.Biosample(**biosample)
        db.add(biosample_db)
    db.commit()


def ingest_data_objects(db: Session, data_object_map: Dict[str, str]):
    data_object_files = [
        DATA / "faa_fna_fastq_data_objects.json",
        DATA / "emsl_data_objects.json",
    ]
    for file in data_object_files:
        for p in load_json_objects(file):
            data_object = load_common_fields(p, include_dates=False)
            if data_object["id"] not in data_object_map:
                # this is a data object with no known project
                continue
            data_object.update(
                {
                    "project_id": data_object_map[data_object["id"]],
                    "file_size_bytes": int(p.pop("file_size_bytes")),
                    "annotations": p,
                }
            )
            data_object_db = models.DataObject(**data_object)
            db.add(data_object_db)
    db.commit()


def main():
    settings = Settings()
    with create_session() as db:
        create_tables(db, settings)
        ingest_studies(db)
        data_object_map = ingest_projects(db)
        ingest_biosamples(db)
        ingest_data_objects(db, data_object_map)


if __name__ == "__main__":
    main()
