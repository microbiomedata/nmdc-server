from collections import defaultdict
from datetime import datetime
import json
from pathlib import Path
import re
from typing import Any, Dict, List, Set, Union
from urllib import request

# from alembic import command
# from alembic.config import Config
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from nmdc_server import crud, database, models, schemas
from nmdc_server.config import Settings
from nmdc_server.database import create_session, metadata

HERE = Path(__file__).parent
DATA = HERE / "data"
NOW = datetime.now().isoformat()
date_re = re.compile(r"^\d{2}$")
# 23-FEB-18 01.10.55.869000000 PM
date_fmt = r"\d\d-[A-Z]+-\d\d \d\d\.\d\d\.\d\d\.\d+ [AP]M"
envo_url = (
    "https://raw.githubusercontent.com/EnvironmentOntology/envo/master/subsets/envo-basic.json"
)

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
    metadata.drop_all()
    metadata.create_all(engine)
    # alembic_cfg = Config(str(HERE / "alembic.ini"))
    # alembic_cfg.set_main_option("sqlalchemy.url", settings.database_uri)
    # command.stamp(alembic_cfg, "head")

    db.query(models.DataObject).delete()
    db.query(models.Biosample).delete()
    db.query(models.Project).delete()
    db.query(models.StudyWebsite).delete()
    db.query(models.StudyPublication).delete()
    db.query(models.Website).delete()
    db.query(models.Publication).delete()
    db.query(models.Study).delete()
    db.query(models.EnvoAncestor).delete()
    db.query(models.EnvoTerm).delete()


def populate_envo_ancestor(
    db: Session,
    term_id: str,
    node: str,
    edges: Dict[str, Set[str]],
    all_nodes: Set[str],
    direct: bool,
    visited: Set[str],
):
    if node in visited:
        raise Exception("Cyclic graph detected")
    if node not in edges:
        return
    visited = visited.union({node})
    for parent in edges[node]:
        if parent not in all_nodes:
            continue  # skip ancestors outside the simplified hierarchy

        statement = insert(models.EnvoAncestor.__table__).values(
            id=term_id, ancestor_id=parent, direct=direct
        )
        if direct:
            statement = statement.on_conflict_do_update(
                index_elements=["id", "ancestor_id"], set_={"direct": True}
            )
        else:
            statement = statement.on_conflict_do_nothing(index_elements=["id", "ancestor_id"])
        db.execute(statement)
    for parent in edges[node]:
        if parent not in all_nodes:
            continue  # skip ancestors outside the simplified hierarchy

        populate_envo_ancestor(db, term_id, parent, edges, all_nodes, False, visited)


def populate_envo(db: Session):
    with request.urlopen(envo_url) as r:
        envo_data = json.load(r)

    for graph in envo_data["graphs"]:
        direct_ancestors: Dict[str, Set[str]] = defaultdict(set)
        for edge in graph["edges"]:
            if edge["pred"] != "is_a":
                continue

            id = edge["sub"].split("/")[-1]
            parent = edge["obj"].split("/")[-1]
            if id != parent:
                direct_ancestors[id].add(parent)

        ids: Set[str] = set()
        for node in graph["nodes"]:
            if not node["id"].startswith("http://purl.obolibrary.org/obo/"):
                continue

            id = node["id"].split("/")[-1]
            label = node.pop("lbl", "")
            data = node.get("meta", {})
            db.add(models.EnvoTerm(id=id, label=label, data=data))
            ids.add(id)

        db.flush()
        for node in ids:
            db.add(models.EnvoAncestor(id=node, ancestor_id=node, direct=False))
            populate_envo_ancestor(db, node, node, direct_ancestors, ids, True, set())

    db.commit()


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


def ingest_projects(db: Session):
    projects = []

    for p in load_json_objects(DATA / "gold_omics_processing.json"):
        assert len(p["part_of"]) == 1
        project = load_common_fields(p)
        project["study_id"] = coerce_id(p.pop("part_of")[0])
        data_objects = p.pop("has_output", [])

        project["annotations"] = p
        projects.append(project)
        project_db = models.Project(**project)

        # https://stackoverflow.com/a/21670302
        db.add(project_db)
        if data_objects:
            db.flush()
            db.execute(
                models.project_output_association.insert().values(
                    [(project_db.id, d) for d in data_objects]
                )
            )

    db.commit()


def ingest_biosamples(db: Session):
    for p in load_json_objects(DATA / "biosample.json"):
        biosample = load_common_fields(p)
        assert len(p["part_of"]) == 1
        lat, lon = p.pop("lat_lon").split(" ")
        env_broad_scale = db.query(models.EnvoTerm).get(p.pop("env_broad_scale"))
        env_local_scale = db.query(models.EnvoTerm).get(p.pop("env_local_scale"))
        env_medium = db.query(models.EnvoTerm).get(p.pop("env_medium"))
        biosample.update(
            {
                "project_id": coerce_id(p.pop("part_of")[0]),
                "latitude": float(lat),
                "longitude": float(lon),
                "env_broad_scale": env_broad_scale,
                "env_local_scale": env_local_scale,
                "env_medium": env_medium,
                "annotations": p,
            }
        )

        if "depth" in biosample["annotations"]:
            biosample["depth"] = float(biosample["annotations"].pop("depth"))

        biosample_db = models.Biosample(**biosample)
        db.add(biosample_db)
    db.commit()


def ingest_data_objects(db: Session):
    data_object_files = [
        DATA / "faa_fna_fastq_data_objects.json",
        DATA / "emsl_data_objects.json",
    ]
    for file in data_object_files:
        for p in load_json_objects(file):
            data_object = load_common_fields(p, include_dates=False)
            data_object.update(
                {"file_size_bytes": int(p.pop("file_size_bytes")),}
            )
            data_object_db = models.DataObject(**data_object)
            db.add(data_object_db)
    db.commit()


def main(*args):
    database.testing = "--testing" in args
    settings = Settings()
    with create_session() as db:
        create_tables(db, settings)
        populate_envo(db)
        ingest_data_objects(db)
        ingest_studies(db)
        ingest_projects(db)
        ingest_biosamples(db)


if __name__ == "__main__":
    import sys

    main(*sys.argv[1:])
